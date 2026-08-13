from __future__ import annotations

import hashlib
import json
import stat
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from scripts.projects.open_model_data import phase3_middle_ukrainian_page_sample as sample
from scripts.projects.open_model_data import phase3_middle_ukrainian_text_extraction as extraction
from scripts.projects.open_model_data.phase3_middle_ukrainian_page_sample import (
    MiddleUkrainianPageSampleError,
)

FAKE_DECODER = """
var DjVu = {
  VERSION: "test-1",
  Document: class {
    constructor(buffer) { this.buffer = buffer; }
    getPagesQuantity() { return 2; }
    getPageUnsafe(number) {
      const width = number === 1 ? 2 : 3;
      const height = number === 1 ? 2 : 1;
      return {
        getWidth() { return width; },
        getHeight() { return height; },
        getDpi() { return 300; },
        getRotation() { return 0; },
        getImageData() {
          const image = new ImageData(width, height);
          for (let index = 0; index < image.data.length; index += 1) {
            image.data[index] = (number * 17 + index) % 256;
          }
          return new ImageData(new Uint8ClampedArray(image.data), width, height);
        },
        reset() {},
      };
    }
  }
};
"""


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _sha256(path: Path) -> str:
    return _sha256_bytes(path.read_bytes())


def _row(
    page_number: int,
    *,
    text: str,
    width: int,
    height: int,
    text_layer_present: bool,
) -> dict[str, Any]:
    text_bytes = text.encode("utf-8")
    zones = [{"x": 0, "y": 0, "width": width, "height": height, "text": text}] if text_layer_present else None
    return {
        "schema_version": extraction.ROW_SCHEMA_VERSION,
        "source_sha256": extraction.intake.SOURCE_SHA256,
        "page_number": page_number,
        "page_width": width,
        "page_height": height,
        "dpi": 300,
        "rotation": 0,
        "text_layer_present": text_layer_present,
        "decoded_text": text,
        "decoded_text_sha256": _sha256_bytes(text_bytes),
        "decoded_text_code_points": len(text),
        "decoded_text_utf8_bytes": len(text_bytes),
        "text_zones": zones,
        "text_zones_sha256": _sha256_bytes(
            json.dumps(zones, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        ),
        "text_zone_count": 1 if text_layer_present else 0,
        "ocr_used": False,
        "normalization_applied": False,
        "inferred_character_repairs": False,
    }


def _selected_metadata(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    reasons = {item["page_number"]: item["reasons"] for item in sample.PAGE_SELECTION}
    return [
        {
            "page_number": row["page_number"],
            "reasons": reasons[row["page_number"]],
            "text_layer_present": row["text_layer_present"],
            "decoded_text_code_points": row["decoded_text_code_points"],
            "decoded_text_utf8_bytes": row["decoded_text_utf8_bytes"],
            "text_zone_count": row["text_zone_count"],
            "page_width": row["page_width"],
            "page_height": row["page_height"],
            "dpi": row["dpi"],
            "rotation": row["rotation"],
            "decoded_text_sha256": row["decoded_text_sha256"],
            "text_zones_sha256": row["text_zones_sha256"],
        }
        for row in rows
    ]


def _patch_fixture_contract(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    *,
    decoder_source: str = FAKE_DECODER,
) -> tuple[Path, Path, Path, bytes]:
    source_path = tmp_path / "fixture.djvu"
    source_path.write_bytes(b"private-page-sample-fixture")
    decoder_path = tmp_path / "decoder.js"
    decoder_path.write_text(decoder_source, encoding="utf-8")
    extraction_dir = tmp_path / "predecessor"
    extraction_dir.mkdir()
    schema_path = tmp_path / "receipt-schema.json"
    schema_path.write_text('{"type":"object"}\n', encoding="utf-8")

    monkeypatch.setattr(extraction.intake, "COLLECTION_ID", "fixture-collection")
    monkeypatch.setattr(extraction.intake, "SOURCE_FILENAME", source_path.name)
    monkeypatch.setattr(extraction.intake, "SOURCE_BYTES", source_path.stat().st_size)
    monkeypatch.setattr(extraction.intake, "SOURCE_SHA256", _sha256(source_path))
    monkeypatch.setattr(extraction, "DECODER_RELEASE_TAG", "test-release")
    monkeypatch.setattr(extraction, "DECODER_ASSET_URL", "https://example.invalid/decoder.js")
    monkeypatch.setattr(extraction, "DECODER_VERSION", "test-1")
    monkeypatch.setattr(extraction, "DECODER_BYTES", decoder_path.stat().st_size)
    monkeypatch.setattr(extraction, "DECODER_SHA256", _sha256(decoder_path))
    monkeypatch.setattr(extraction, "EXPECTED_PAGES", 2)
    monkeypatch.setattr(extraction, "EXPECTED_TEXT_LAYER_PAGES", 1)
    monkeypatch.setattr(
        sample,
        "PAGE_SELECTION",
        (
            {"page_number": 1, "reasons": ["front_matter_cover"]},
            {"page_number": 2, "reasons": ["missing_text_layer"]},
        ),
    )
    monkeypatch.setattr(sample, "SELECTED_PAGES", (1, 2))
    monkeypatch.setattr(sample, "RECEIPT_SCHEMA_PATH", schema_path)

    rows = [
        _row(1, text="тест", width=2, height=2, text_layer_present=True),
        _row(2, text="", width=3, height=1, text_layer_present=False),
    ]
    predecessor_payload = b"".join(
        (json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n").encode("utf-8") for row in rows
    )
    predecessor_path = extraction_dir / extraction.PRIVATE_JSONL_FILENAME
    predecessor_path.write_bytes(predecessor_payload)
    predecessor_path.chmod(0o600)
    monkeypatch.setattr(sample, "EXTRACTION_PRIVATE_JSONL_SHA256", _sha256(predecessor_path))
    monkeypatch.setattr(sample, "EXTRACTION_RECEIPT_FILE_SHA256", "1" * 64)
    monkeypatch.setattr(sample, "EXTRACTION_RECEIPT_SHA256", "2" * 64)
    monkeypatch.setattr(
        extraction,
        "validate_existing_extraction",
        lambda **_kwargs: {
            "receipt_file_sha256": sample.EXTRACTION_RECEIPT_FILE_SHA256,
            "receipt_sha256": sample.EXTRACTION_RECEIPT_SHA256,
            "private_jsonl_sha256": sample.EXTRACTION_PRIVATE_JSONL_SHA256,
        },
    )
    monkeypatch.setattr(sample, "_validate_selection", lambda value: _selected_metadata(list(value)))
    return source_path, decoder_path, extraction_dir, predecessor_payload


def _materialize_fixture(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> tuple[Path, Path, Path, Path, bytes, dict[str, Any]]:
    source_path, decoder_path, extraction_dir, predecessor_payload = _patch_fixture_contract(monkeypatch, tmp_path)
    output_dir = tmp_path / "private-output"
    result = sample.materialize_page_sample(
        source_path=source_path,
        raw_intake_dir=tmp_path / "raw-intake",
        extraction_dir=extraction_dir,
        decoder_path=decoder_path,
        private_output_dir=output_dir,
    )
    return source_path, decoder_path, extraction_dir, output_dir, predecessor_payload, result


def test_materialize_and_replay_private_page_sample(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source_path, _decoder_path, extraction_dir, output_dir, predecessor_payload, result = _materialize_fixture(
        tmp_path, monkeypatch
    )
    replay = sample.validate_existing_page_sample(
        source_path=source_path,
        raw_intake_dir=tmp_path / "raw-intake",
        extraction_dir=extraction_dir,
        private_output_dir=output_dir,
    )

    assert result == replay
    assert replay["sample_pages"] == 2
    assert replay["sample_text_layer_pages"] == 1
    assert replay["sample_missing_text_layer_pages"] == 1
    assert replay["packet_ready_for_qualified_review"] is True
    assert replay["review_response_status"] == "pending"
    assert replay["training_eligible"] is False
    assert replay["phase3_complete"] is False
    assert replay["phase4_blocked"] is True
    assert replay["provider_calls"] is False
    assert (output_dir / sample.SELECTED_JSONL_FILENAME).read_bytes() == predecessor_payload
    assert stat.S_IMODE(output_dir.stat().st_mode) == 0o700
    for path in output_dir.rglob("*"):
        if path.is_file():
            assert stat.S_IMODE(path.stat().st_mode) == 0o600
    receipt = json.loads((output_dir / sample.RECEIPT_FILENAME).read_text(encoding="utf-8"))
    assert receipt["private_packet"]["image_count"] == 2
    assert receipt["rendering"]["lossless_png"] is True
    assert receipt["review_contract"]["embedded_text_quality_verified"] is False


@pytest.mark.parametrize(
    ("relative_path", "mutation", "message"),
    [
        (
            sample.SELECTED_JSONL_FILENAME,
            lambda payload: payload.replace("тест".encode(), "теср".encode()),
            "selected private",
        ),
        (sample.REVIEW_HTML_FILENAME, lambda payload: payload + b"<!--tamper-->", "review HTML drift"),
        (
            sample.REVIEW_TEMPLATE_FILENAME,
            lambda payload: payload.replace(b'"pending"', b'"changed"', 1),
            "response template drift",
        ),
        ("page-images/page-001.png", lambda payload: payload + b"x", "page image"),
    ],
)
def test_private_packet_tamper_is_rejected(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    relative_path: str,
    mutation: Any,
    message: str,
) -> None:
    source_path, _decoder_path, extraction_dir, output_dir, _payload, _result = _materialize_fixture(
        tmp_path, monkeypatch
    )
    target = output_dir / relative_path
    target.write_bytes(mutation(target.read_bytes()))

    with pytest.raises(MiddleUkrainianPageSampleError, match=message):
        sample.validate_existing_page_sample(
            source_path=source_path,
            raw_intake_dir=tmp_path / "raw-intake",
            extraction_dir=extraction_dir,
            private_output_dir=output_dir,
        )


def test_existing_private_output_is_immutable(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source_path, decoder_path, extraction_dir, _payload = _patch_fixture_contract(monkeypatch, tmp_path)
    output_dir = tmp_path / "private-output"
    output_dir.mkdir()

    with pytest.raises(MiddleUkrainianPageSampleError, match="already exists"):
        sample.materialize_page_sample(
            source_path=source_path,
            raw_intake_dir=tmp_path / "raw-intake",
            extraction_dir=extraction_dir,
            decoder_path=decoder_path,
            private_output_dir=output_dir,
        )


@pytest.mark.parametrize(
    ("relative_path", "mode", "message"),
    [
        (".", 0o755, "page-sample directory permissions drift"),
        (sample.SELECTED_JSONL_FILENAME, 0o644, "selected private page text permissions drift"),
        (sample.IMAGE_DIRECTORY_NAME, 0o755, "page image directory permissions drift"),
        ("page-images/page-001.png", 0o644, "page image page-001.png permissions drift"),
    ],
)
def test_private_permission_drift_is_rejected(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    relative_path: str,
    mode: int,
    message: str,
) -> None:
    source_path, _decoder_path, extraction_dir, output_dir, _payload, _result = _materialize_fixture(
        tmp_path, monkeypatch
    )
    (output_dir / relative_path).chmod(mode)

    with pytest.raises(MiddleUkrainianPageSampleError, match=message):
        sample.validate_existing_page_sample(
            source_path=source_path,
            raw_intake_dir=tmp_path / "raw-intake",
            extraction_dir=extraction_dir,
            private_output_dir=output_dir,
        )


def test_private_output_inside_git_checkout_is_rejected(tmp_path: Path) -> None:
    checkout = tmp_path / "checkout"
    checkout.mkdir()
    (checkout / ".git").write_text("gitdir: elsewhere\n", encoding="utf-8")

    with pytest.raises(MiddleUkrainianPageSampleError, match="inside Git"):
        sample.materialize_page_sample(
            source_path=tmp_path / "missing.djvu",
            raw_intake_dir=tmp_path / "missing-intake",
            extraction_dir=tmp_path / "missing-extraction",
            decoder_path=tmp_path / "missing.js",
            private_output_dir=checkout / "private-output",
        )


def test_renderer_failure_removes_partial_images(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    decoder_source = FAKE_DECODER.replace(
        "const image = new ImageData(width, height);",
        'if (number === 2) throw new Error("forced render failure");\n          const image = new ImageData(width, height);',
    )
    source_path, decoder_path, _extraction_dir, _payload = _patch_fixture_contract(
        monkeypatch, tmp_path, decoder_source=decoder_source
    )
    image_directory = tmp_path / "images"
    image_directory.mkdir()

    with pytest.raises(MiddleUkrainianPageSampleError, match="page render failed"):
        sample._invoke_renderer(
            source_path=source_path,
            decoder_path=decoder_path,
            image_directory=image_directory,
        )
    assert not list(image_directory.iterdir())


def test_renderer_rejects_nonempty_image_directory(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source_path, decoder_path, _extraction_dir, _payload = _patch_fixture_contract(monkeypatch, tmp_path)
    image_directory = tmp_path / "images"
    image_directory.mkdir()
    (image_directory / "unexpected").write_bytes(b"x")

    with pytest.raises(MiddleUkrainianPageSampleError, match="image output directory is not empty"):
        sample._invoke_renderer(
            source_path=source_path,
            decoder_path=decoder_path,
            image_directory=image_directory,
        )


def test_renderer_rejects_decoder_drift(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source_path, decoder_path, _extraction_dir, _payload = _patch_fixture_contract(monkeypatch, tmp_path)
    image_directory = tmp_path / "images"
    image_directory.mkdir()
    decoder_path.write_text(FAKE_DECODER + "\n", encoding="utf-8")

    with pytest.raises(MiddleUkrainianPageSampleError, match="decoder SHA-256 drift"):
        sample._invoke_renderer(
            source_path=source_path,
            decoder_path=decoder_path,
            image_directory=image_directory,
        )
    assert not list(image_directory.iterdir())


def test_materialization_failure_cleans_staging_directory(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source_path, decoder_path, extraction_dir, _payload = _patch_fixture_contract(monkeypatch, tmp_path)
    output_dir = tmp_path / "private-output"

    def reject(_receipt: object) -> None:
        raise MiddleUkrainianPageSampleError("forced receipt failure")

    monkeypatch.setattr(sample, "_validate_receipt", reject)
    with pytest.raises(MiddleUkrainianPageSampleError, match="forced receipt failure"):
        sample.materialize_page_sample(
            source_path=source_path,
            raw_intake_dir=tmp_path / "raw-intake",
            extraction_dir=extraction_dir,
            decoder_path=decoder_path,
            private_output_dir=output_dir,
        )
    assert not output_dir.exists()
    assert not list(tmp_path.glob(".private-output.stage-*"))


def test_production_selection_rederives_structural_anchors() -> None:
    rows = [
        _row(
            page_number,
            text="x" * (3_432 if page_number == 163 else page_number),
            width=4_356 if page_number == 196 else 3_594,
            height=4_980,
            text_layer_present=page_number not in {3, 196},
        )
        for page_number in range(1, 197)
    ]

    selected = sample._validate_selection(rows)

    assert [item["page_number"] for item in selected] == list(sample.SELECTED_PAGES)
    assert sum(bool(item["text_layer_present"]) for item in selected) == 14
    assert selected[-1]["reasons"] == ["missing_text_layer", "alternate_geometry", "terminal_page"]


def test_production_selection_rejects_source_fact_drift() -> None:
    rows = [
        _row(
            page_number,
            text="x" * (3_432 if page_number == 162 else page_number),
            width=4_356 if page_number == 196 else 3_594,
            height=4_980,
            text_layer_present=page_number not in {3, 196},
        )
        for page_number in range(1, 197)
    ]

    with pytest.raises(MiddleUkrainianPageSampleError, match="maximum-density source fact drift"):
        sample._validate_selection(rows)


def test_schema_error_sort_handles_mixed_array_and_object_paths(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    schema_path = tmp_path / "mixed-path-schema.json"
    schema_path.write_text("{}\n", encoding="utf-8")
    monkeypatch.setattr(sample, "RECEIPT_SCHEMA_PATH", schema_path)

    class MixedPathValidator:
        def __init__(self, _schema: object) -> None:
            pass

        @staticmethod
        def check_schema(_schema: object) -> None:
            pass

        def iter_errors(self, _receipt: object) -> list[SimpleNamespace]:
            return [
                SimpleNamespace(absolute_path=("a", 0), path=("a", 0), message="array error"),
                SimpleNamespace(absolute_path=("a", "b"), path=("a", "b"), message="object error"),
            ]

    monkeypatch.setattr(sample, "Draft202012Validator", MixedPathValidator)

    with pytest.raises(MiddleUkrainianPageSampleError, match="receipt schema violation"):
        sample._validate_receipt({"receipt_sha256": "0" * 64})


def test_receipt_schema_is_text_free_source_bound_and_fail_closed() -> None:
    schema = json.loads(sample.RECEIPT_SCHEMA_PATH.read_text(encoding="utf-8"))
    serialized = json.dumps(schema, ensure_ascii=False)
    source = schema["properties"]["source_binding"]["properties"]

    assert '"decoded_text"' not in serialized
    assert '"text_zones"' not in serialized
    assert source["collection_id"]["const"] == extraction.intake.COLLECTION_ID
    assert source["predecessor_extraction_receipt_file_sha256"]["const"] == sample.EXTRACTION_RECEIPT_FILE_SHA256
    assert source["predecessor_extraction_receipt_sha256"]["const"] == sample.EXTRACTION_RECEIPT_SHA256
    assert source["predecessor_private_jsonl_sha256"]["const"] == sample.EXTRACTION_PRIVATE_JSONL_SHA256
    assert schema["properties"]["review_contract"]["properties"]["review_response_status"] == {"const": "pending"}
    assert schema["properties"]["safeguards"]["properties"]["training_eligible"] == {"const": False}
    assert schema["properties"]["safeguards"]["properties"]["phase3_complete"] == {"const": False}
    assert schema["properties"]["safeguards"]["properties"]["phase4_blocked"] == {"const": True}
