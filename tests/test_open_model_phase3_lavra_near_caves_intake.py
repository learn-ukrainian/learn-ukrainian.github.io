from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.projects.open_model_data import phase3_lavra_near_caves_intake as intake
from scripts.projects.open_model_data.phase3_lavra_near_caves_intake import LavraNearCavesIntakeError


def _page(text: str, font_tags: list[str]) -> dict[str, object]:
    return {
        "text": text,
        "text_sha256": intake._sha256_text(text),
        "font_tags": font_tags,
        "legacy_font_spans": intake._legacy_font_spans(text, font_tags),
    }


def _fixture_pages() -> dict[int, dict[str, object]]:
    base = "/FIXTURE+CyrillicaBEM-Normal"
    return {
        166: _page("article page", ["/Fixture+Times"] * len("article page")),
        167: _page("xOLDy", ["/Fixture+Times", base, base, base, "/Fixture+Times"]),
    }


def _patch_fixture_contract(monkeypatch: pytest.MonkeyPatch, schema_path: Path) -> None:
    pages = _fixture_pages()
    monkeypatch.setattr(intake, "RECEIPT_SCHEMA_PATH", schema_path)
    monkeypatch.setattr(intake, "EXPECTED_ARTICLE_PAGES", 2)
    monkeypatch.setattr(intake, "EXPECTED_NATIVE_TEXT_CHARACTERS", sum(len(page["text"]) for page in pages.values()))
    monkeypatch.setattr(intake, "EXPECTED_PAGES_WITH_LEGACY_FONT", 1)
    monkeypatch.setattr(intake, "EXPECTED_LEGACY_FONT_SPANS", 1)
    monkeypatch.setattr(intake, "EXPECTED_LEGACY_FONT_CHARACTERS", 3)
    monkeypatch.setattr(intake, "EXPECTED_LEGACY_FONT_NONSPACE_CHARACTERS", 3)
    monkeypatch.setattr(
        intake,
        "EXPECTED_LEGACY_FONT_BASE_NAME_COUNTS",
        {"/FIXTURE+CyrillicaBEM-Normal": 3},
    )
    monkeypatch.setattr(intake, "_validate_retrieval_receipt", lambda _path: {})
    monkeypatch.setattr(intake, "load_article_pages", lambda _path: pages)


def test_legacy_font_spans_preserve_exact_offsets_and_text() -> None:
    text = "aOLD zXY"
    legacy = "/Fixture+CyrillicaBEM-Normal"
    tags = ["/Fixture+Times", legacy, legacy, legacy, "/Fixture+Times", "/Fixture+Times", legacy, legacy]

    spans = intake._legacy_font_spans(text, tags)

    assert [(span["start_char"], span["end_char"], span["raw_text"]) for span in spans] == [
        (1, 4, "OLD"),
        (6, 8, "XY"),
    ]
    assert all(span["encoding_status"] == "legacy_font_unresolved_no_unicode_claim" for span in spans)


def test_font_tag_alignment_drift_is_rejected() -> None:
    with pytest.raises(LavraNearCavesIntakeError, match="font tag alignment drift"):
        intake._legacy_font_spans("abc", ["/Fixture+Times"])


def test_private_record_is_direct_evidence_but_not_training_gold() -> None:
    page = _fixture_pages()[167]

    record = intake.build_page_record(167, page)

    assert record["source_text"] == "xOLDy"
    assert record["legacy_font_spans"][0]["raw_text"] == "OLD"
    assert record["direct_lavra_near_caves_evidence"] is True
    assert record["source_attributed_reading_only"] is True
    assert record["legacy_encoding_resolved"] is False
    assert record["inferred_character_repairs"] is False
    assert record["semantic_gold"] is False
    assert record["training_eligible"] is False
    assert record["modern_correction_eligible"] is False
    assert record["phase4_authorized"] is False


def test_private_record_tamper_is_rejected() -> None:
    page = _fixture_pages()[167]
    record = intake.build_page_record(167, page)
    record["training_eligible"] = True

    with pytest.raises(LavraNearCavesIntakeError, match="unsafe private record flag"):
        intake._validate_page_record(record, page, 167)


def test_retrieval_receipt_is_bound_to_source_and_safety(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    receipt_path = tmp_path / "retrieval.json"
    receipt = {
        "schema_version": "phase3_historical_source_retrieval_receipt_v1",
        "source": {
            "title": intake.SOURCE_TITLE,
            "author": intake.SOURCE_AUTHOR,
            "year": intake.SOURCE_YEAR,
            "landing_or_file_url": intake.SOURCE_URL,
        },
        "custody": {
            "sha256": intake.SOURCE_PDF_SHA256,
            "pdf_pages": intake.EXPECTED_PDF_PAGES,
            "storage": "private_google_drive",
        },
        "phase3_scope": {
            "direct_inscription_evidence": True,
            "training_admitted": False,
            "phase4_blocked": True,
        },
    }
    receipt_path.write_text(json.dumps(receipt), encoding="utf-8")
    monkeypatch.setattr(intake, "RETRIEVAL_RECEIPT_SHA256", intake.file_sha256(receipt_path))

    intake._validate_retrieval_receipt(receipt_path)
    receipt["phase3_scope"]["training_admitted"] = True
    receipt_path.write_text(json.dumps(receipt), encoding="utf-8")
    monkeypatch.setattr(intake, "RETRIEVAL_RECEIPT_SHA256", intake.file_sha256(receipt_path))

    with pytest.raises(LavraNearCavesIntakeError, match="cannot admit training"):
        intake._validate_retrieval_receipt(receipt_path)


def test_materialize_and_validate_are_deterministic_and_fail_on_tamper(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    schema_path = tmp_path / "schema.json"
    schema_path.write_text('{"type":"object"}\n', encoding="utf-8")
    _patch_fixture_contract(monkeypatch, schema_path)
    private_dir = tmp_path / "private"

    receipt = intake.materialize_intake(
        pdf_path=tmp_path / "source.pdf",
        retrieval_receipt_path=tmp_path / "retrieval.json",
        private_output_dir=private_dir,
    )
    validated = intake.validate_existing_intake(
        pdf_path=tmp_path / "source.pdf",
        retrieval_receipt_path=tmp_path / "retrieval.json",
        private_output_dir=private_dir,
    )

    assert receipt["denominator"] == {
        "article_pages": 2,
        "nonempty_native_text_pages": 2,
        "native_text_characters": 17,
        "pages_with_legacy_cyrillica": 1,
        "legacy_cyrillica_spans": 1,
        "legacy_cyrillica_characters": 3,
        "legacy_cyrillica_nonspace_characters": 3,
        "legacy_font_base_name_counts": {"/FIXTURE+CyrillicaBEM-Normal": 3},
    }
    assert validated["records"] == 2
    assert validated["training_eligible"] is False
    assert validated["phase4_authorized"] is False

    output_path = private_dir / intake.OUTPUT_FILENAME
    output_path.write_bytes(output_path.read_bytes() + b"tamper")
    with pytest.raises(LavraNearCavesIntakeError, match="byte count drift"):
        intake.validate_existing_intake(
            pdf_path=tmp_path / "source.pdf",
            retrieval_receipt_path=tmp_path / "retrieval.json",
            private_output_dir=private_dir,
        )


def test_same_length_private_output_corruption_fails_sha256_guard(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    schema_path = tmp_path / "schema.json"
    schema_path.write_text('{"type":"object"}\n', encoding="utf-8")
    _patch_fixture_contract(monkeypatch, schema_path)
    private_dir = tmp_path / "private"
    intake.materialize_intake(
        pdf_path=tmp_path / "source.pdf",
        retrieval_receipt_path=tmp_path / "retrieval.json",
        private_output_dir=private_dir,
    )
    output_path = private_dir / intake.OUTPUT_FILENAME
    corrupted = bytearray(output_path.read_bytes())
    corrupted[len(corrupted) // 2] ^= 1
    output_path.write_bytes(corrupted)

    with pytest.raises(LavraNearCavesIntakeError, match="SHA-256 drift"):
        intake.validate_existing_intake(
            pdf_path=tmp_path / "source.pdf",
            retrieval_receipt_path=tmp_path / "retrieval.json",
            private_output_dir=private_dir,
        )


def test_private_output_inside_git_checkout_is_rejected(tmp_path: Path) -> None:
    checkout = tmp_path / "checkout"
    checkout.mkdir()
    (checkout / ".git").mkdir()

    with pytest.raises(LavraNearCavesIntakeError, match="cannot be written inside Git"):
        intake.materialize_intake(
            pdf_path=tmp_path / "source.pdf",
            retrieval_receipt_path=tmp_path / "retrieval.json",
            private_output_dir=checkout / "private",
        )


def test_materialization_failure_leaves_no_partial_artifacts(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    schema_path = tmp_path / "schema.json"
    schema_path.write_text('{"type":"object"}\n', encoding="utf-8")
    _patch_fixture_contract(monkeypatch, schema_path)
    private_dir = tmp_path / "private"

    def reject_receipt(_receipt: object) -> None:
        raise LavraNearCavesIntakeError("forced receipt failure")

    monkeypatch.setattr(intake, "_validate_receipt", reject_receipt)
    with pytest.raises(LavraNearCavesIntakeError, match="forced receipt failure"):
        intake.materialize_intake(
            pdf_path=tmp_path / "source.pdf",
            retrieval_receipt_path=tmp_path / "retrieval.json",
            private_output_dir=private_dir,
        )

    assert not private_dir.exists()


def test_existing_private_output_directory_is_immutable(tmp_path: Path) -> None:
    private_dir = tmp_path / "private"
    private_dir.mkdir()

    with pytest.raises(LavraNearCavesIntakeError, match="already exists"):
        intake.materialize_intake(
            pdf_path=tmp_path / "source.pdf",
            retrieval_receipt_path=tmp_path / "retrieval.json",
            private_output_dir=private_dir,
        )


def test_public_receipt_schema_forbids_source_text() -> None:
    schema = json.loads(intake.RECEIPT_SCHEMA_PATH.read_text(encoding="utf-8"))
    assert '"source_text"' not in json.dumps(schema, ensure_ascii=False)
    assert schema["properties"]["safeguards"]["properties"]["public_repo_contains_source_text"] == {"const": False}
