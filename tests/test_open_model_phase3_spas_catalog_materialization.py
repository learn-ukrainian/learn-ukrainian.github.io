from __future__ import annotations

import gzip
import json
from copy import deepcopy
from pathlib import Path

import pytest

from scripts.projects.open_model_data import phase3_spas_catalog_materialization as materialization
from scripts.projects.open_model_data.phase3_spas_catalog_materialization import (
    SpasCatalogMaterializationError,
    split_catalog_records,
)


def _pages() -> dict[int, str]:
    return {
        15: "Графіті № 1 (табл. I)\nПерший запис.\n",
        16: (
            "Продовження першого.\n"
            "Графіті № 2 (табл. II)\nДругий \ue002 запис.\n"
            "Графіті № 3 (табл. III)\nТретій запис."
        ),
    }


def _patch_fixture_identity(monkeypatch: pytest.MonkeyPatch) -> None:
    pages = _pages()
    monkeypatch.setattr(materialization, "SOURCE_PDF_SHA256", "a" * 64)
    monkeypatch.setattr(materialization, "EXPECTED_PDF_PAGES", 2)
    monkeypatch.setattr(materialization, "CATALOG_PDF_PAGE_START", 15)
    monkeypatch.setattr(materialization, "CATALOG_PDF_PAGE_END", 16)
    monkeypatch.setattr(materialization, "EXPECTED_CATALOG_RECORDS", 3)
    monkeypatch.setattr(materialization, "EXPECTED_NATIVE_TEXT_CHARACTERS", sum(len(text) for text in pages.values()))
    monkeypatch.setattr(materialization, "EXPECTED_PRIVATE_USE_COUNTS", {"U+E002": 1})


def _materialize(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, *, name: str = "private") -> dict[str, object]:
    pages = _pages()
    monkeypatch.setattr(materialization, "load_catalog_pages", lambda *_args, **_kwargs: deepcopy(pages))
    output = tmp_path / name
    return materialization.materialize_spas_catalog(
        pdf_path=tmp_path / "not-read.pdf",
        private_output_dir=output,
        receipt_output=output / materialization.RECEIPT_FILENAME,
        expected_pdf_sha256="a" * 64,
        expected_pdf_pages=2,
        catalog_pdf_page_start=15,
        catalog_pdf_page_end=16,
        expected_record_count=3,
        expected_native_text_characters=sum(len(text) for text in pages.values()),
        expected_private_use_counts={"U+E002": 1},
    )


def test_splits_exact_sequential_headings_and_preserves_page_offsets() -> None:
    pages = _pages()
    records = split_catalog_records(pages, expected_record_count=3, source_pdf_sha256="a" * 64)

    assert [record["graffito_number"] for record in records] == [1, 2, 3]
    assert records[0]["source_text"] == (
        "Графіті № 1 (табл. I)\nПерший запис.\n\nПродовження першого.\n"
    )
    assert records[0]["source_page_fragments"] == [
        {
            "pdf_page_number": 15,
            "start_char": 0,
            "end_char": len(pages[15]),
            "text_sha256": materialization.hashlib.sha256(pages[15].encode()).hexdigest(),
        },
        {
            "pdf_page_number": 16,
            "start_char": 0,
            "end_char": pages[16].index("Графіті № 2"),
            "text_sha256": materialization.hashlib.sha256("Продовження першого.\n".encode()).hexdigest(),
        },
    ]
    assert records[1]["private_use_codepoint_counts"] == {"U+E002": 1}
    assert records[1]["contains_private_use_glyphs"] is True
    assert records[1]["normalization_status"] == "not_applied"
    assert records[1]["training_eligible"] is False
    assert records[1]["modern_correction_eligible"] is False
    assert records[1]["ocr_used"] is False
    assert records[1]["images_included"] is False


@pytest.mark.parametrize(
    "text",
    [
        "Графіті № 1\nОдин.\nГрафіті № 3\nТри.",
        "Графіті № 1\nОдин.\nГрафіті № 1\nЩе один.\nГрафіті № 2\nДва.",
    ],
)
def test_rejects_missing_or_duplicate_record_numbers(text: str) -> None:
    with pytest.raises(SpasCatalogMaterializationError, match="exact sequential range"):
        split_catalog_records({15: text}, expected_record_count=2)


def test_rejects_noncontiguous_catalogue_pages() -> None:
    with pytest.raises(SpasCatalogMaterializationError, match="must be contiguous"):
        split_catalog_records({15: "Графіті № 1\nОдин.", 17: "Графіті № 2\nДва."}, expected_record_count=2)


def test_next_heading_at_page_start_does_not_create_an_empty_fragment() -> None:
    pages = {
        15: "Графіті № 1\nОдин.",
        16: "Графіті № 2\nДва.",
    }
    records = split_catalog_records(pages, expected_record_count=2)

    assert records[0]["source_text"] == pages[15]
    assert [fragment["pdf_page_number"] for fragment in records[0]["source_page_fragments"]] == [15]
    assert records[1]["source_text"] == pages[16]


def test_rejects_replacement_characters() -> None:
    with pytest.raises(SpasCatalogMaterializationError, match="replacement characters"):
        split_catalog_records({15: "Графіті № 1\nПошкоджено \ufffd."}, expected_record_count=1)


def test_materialization_writes_private_jsonl_and_text_free_sealed_receipt(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    receipt = _materialize(tmp_path, monkeypatch)
    output = tmp_path / "private"

    with gzip.open(output / materialization.OUTPUT_FILENAME, "rt", encoding="utf-8") as handle:
        rows = [json.loads(line) for line in handle]
    persisted_receipt = json.loads((output / materialization.RECEIPT_FILENAME).read_text(encoding="utf-8"))

    assert len(rows) == 3
    assert rows[0]["source_pdf_sha256"] == "a" * 64
    assert receipt == persisted_receipt
    assert receipt["denominator"]["materialized_records"] == 3
    assert receipt["private_use_audit"]["codepoint_counts"] == {"U+E002": 1}
    assert receipt["rights_and_scope"]["bounded_text_first_use_decision"] == "accepted_operational_risk"
    assert receipt["safeguards"]["training_eligible"] is False
    assert receipt["safeguards"]["normalized_historical_text_emitted"] is False
    assert receipt["residuals"]["lavra_cave_corpus_gap_closed"] is False
    assert "Перший запис" not in json.dumps(receipt, ensure_ascii=False)
    materialization._validate_receipt(receipt)


def test_materialization_is_byte_deterministic(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    first = _materialize(tmp_path, monkeypatch, name="first")
    second = _materialize(tmp_path, monkeypatch, name="second")

    assert first["output"]["sha256"] == second["output"]["sha256"]
    assert first["output"]["record_identity_manifest_sha256"] == second["output"][
        "record_identity_manifest_sha256"
    ]
    assert first["receipt_sha256"] == second["receipt_sha256"]


def test_existing_materialization_rebinds_every_record_to_source_pages(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    receipt = _materialize(tmp_path, monkeypatch)
    _patch_fixture_identity(monkeypatch)
    validation = materialization.validate_existing_materialization(
        pdf_path=tmp_path / "not-read.pdf",
        private_output_dir=tmp_path / "private",
    )

    assert validation == {
        "ok": True,
        "records": 3,
        "source_pdf_sha256": "a" * 64,
        "private_jsonl_sha256": receipt["output"]["sha256"],
        "receipt_sha256": receipt["receipt_sha256"],
        "training_eligible": False,
    }


def test_existing_materialization_rejects_private_output_tamper(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _materialize(tmp_path, monkeypatch)
    _patch_fixture_identity(monkeypatch)
    output = tmp_path / "private" / materialization.OUTPUT_FILENAME
    output.write_bytes(output.read_bytes() + b"tamper")

    with pytest.raises(SpasCatalogMaterializationError, match="byte count drift"):
        materialization.validate_existing_materialization(
            pdf_path=tmp_path / "not-read.pdf",
            private_output_dir=tmp_path / "private",
        )


def test_existing_materialization_rejects_same_length_private_output_tamper(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _materialize(tmp_path, monkeypatch)
    _patch_fixture_identity(monkeypatch)
    output = tmp_path / "private" / materialization.OUTPUT_FILENAME
    payload = bytearray(output.read_bytes())
    payload[len(payload) // 2] ^= 1
    output.write_bytes(payload)

    with pytest.raises(SpasCatalogMaterializationError, match="SHA-256 drift"):
        materialization.validate_existing_materialization(
            pdf_path=tmp_path / "not-read.pdf",
            private_output_dir=tmp_path / "private",
        )


def test_existing_materialization_rejects_receipt_source_identity_substitution(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _materialize(tmp_path, monkeypatch)
    _patch_fixture_identity(monkeypatch)
    receipt_path = tmp_path / "private" / materialization.RECEIPT_FILENAME
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    receipt["inputs"]["source_pdf_sha256"] = "b" * 64
    body = {key: value for key, value in receipt.items() if key != "receipt_sha256"}
    receipt["receipt_sha256"] = materialization.sha256_value(body)
    receipt_path.write_text(json.dumps(receipt), encoding="utf-8")

    with pytest.raises(SpasCatalogMaterializationError, match="source PDF identity drift"):
        materialization.validate_existing_materialization(
            pdf_path=tmp_path / "not-read.pdf",
            private_output_dir=tmp_path / "private",
        )


def test_existing_materialization_rejects_receipt_record_denominator_substitution(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _materialize(tmp_path, monkeypatch)
    _patch_fixture_identity(monkeypatch)
    receipt_path = tmp_path / "private" / materialization.RECEIPT_FILENAME
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    for field in ("expected_records", "materialized_records", "unique_record_numbers"):
        receipt["denominator"][field] = 2
    receipt["output"]["records"] = 2
    body = {key: value for key, value in receipt.items() if key != "receipt_sha256"}
    receipt["receipt_sha256"] = materialization.sha256_value(body)
    receipt_path.write_text(json.dumps(receipt), encoding="utf-8")

    with pytest.raises(SpasCatalogMaterializationError, match="record-count identity drift"):
        materialization.validate_existing_materialization(
            pdf_path=tmp_path / "not-read.pdf",
            private_output_dir=tmp_path / "private",
        )


def test_raw_record_fragment_hash_tamper_is_rejected() -> None:
    pages = _pages()
    record = split_catalog_records(pages, expected_record_count=3)[0]
    record["source_page_fragments"][0]["text_sha256"] = "0" * 64

    with pytest.raises(SpasCatalogMaterializationError, match="fragment hash drift"):
        materialization._validate_raw_record(
            record,
            expected_number=1,
            expected_pdf_sha256=materialization.SOURCE_PDF_SHA256,
            page_texts=pages,
        )


def test_existing_materialization_rejects_manifest_hash_tamper(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _materialize(tmp_path, monkeypatch)
    _patch_fixture_identity(monkeypatch)
    receipt_path = tmp_path / "private" / materialization.RECEIPT_FILENAME
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    receipt["output"]["record_identity_manifest_sha256"] = "0" * 64
    body = {key: value for key, value in receipt.items() if key != "receipt_sha256"}
    receipt["receipt_sha256"] = materialization.sha256_value(body)
    receipt_path.write_text(json.dumps(receipt), encoding="utf-8")

    with pytest.raises(SpasCatalogMaterializationError, match="record identity manifest drift"):
        materialization.validate_existing_materialization(
            pdf_path=tmp_path / "not-read.pdf",
            private_output_dir=tmp_path / "private",
        )


def test_materialization_refuses_to_overwrite_immutable_output(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _materialize(tmp_path, monkeypatch)
    with pytest.raises(SpasCatalogMaterializationError, match="already exists"):
        _materialize(tmp_path, monkeypatch)


def test_materialization_refuses_directory_that_appears_during_publication(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    original_write_receipt = materialization._write_receipt

    def create_competing_output(path: Path, receipt: dict[str, object]) -> None:
        original_write_receipt(path, receipt)
        (tmp_path / "private").mkdir()

    monkeypatch.setattr(materialization, "_write_receipt", create_competing_output)
    with pytest.raises(SpasCatalogMaterializationError, match="appeared during publication"):
        _materialize(tmp_path, monkeypatch)
    assert list((tmp_path / "private").iterdir()) == []


def test_materialization_rejects_private_output_inside_git_checkout(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    (tmp_path / ".git").mkdir()
    pages = _pages()
    monkeypatch.setattr(materialization, "load_catalog_pages", lambda *_args, **_kwargs: deepcopy(pages))
    output = tmp_path / "private"
    with pytest.raises(SpasCatalogMaterializationError, match="cannot be inside a Git checkout"):
        materialization.materialize_spas_catalog(
            pdf_path=tmp_path / "not-read.pdf",
            private_output_dir=output,
            receipt_output=output / materialization.RECEIPT_FILENAME,
            expected_record_count=3,
            expected_native_text_characters=sum(len(text) for text in pages.values()),
            expected_private_use_counts={"U+E002": 1},
        )


def test_load_catalog_pages_rejects_source_hash_drift(tmp_path: Path) -> None:
    pdf = tmp_path / "source.pdf"
    pdf.write_bytes(b"not the immutable source")
    with pytest.raises(SpasCatalogMaterializationError, match="SHA-256 mismatch"):
        materialization.load_catalog_pages(pdf, expected_pdf_sha256="0" * 64)


def test_receipt_tamper_is_rejected(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    receipt = _materialize(tmp_path, monkeypatch)
    tampered = deepcopy(receipt)
    tampered["safeguards"]["training_eligible"] = True
    with pytest.raises(SpasCatalogMaterializationError, match="schema violation"):
        materialization._validate_receipt(tampered)


def test_receipt_cross_field_tamper_is_rejected(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    receipt = _materialize(tmp_path, monkeypatch)
    tampered = deepcopy(receipt)
    tampered["denominator"]["unique_record_numbers"] = 2
    body = {key: value for key, value in tampered.items() if key != "receipt_sha256"}
    tampered["receipt_sha256"] = materialization.sha256_value(body)

    with pytest.raises(SpasCatalogMaterializationError, match="record denominator drift"):
        materialization._validate_receipt(tampered)
