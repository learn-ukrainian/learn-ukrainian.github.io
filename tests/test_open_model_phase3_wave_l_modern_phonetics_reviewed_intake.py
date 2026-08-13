from __future__ import annotations

import hashlib
import json
import os
import stat
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from scripts.projects.open_model_data import phase3_wave_l_modern_phonetics_reviewed_intake as intake


class _FakePage:
    def __init__(self, count: int) -> None:
        self._count = count

    def extract_text(self) -> str:
        return f"page {self._count} text"


class _FakeReader:
    def __init__(self, page_count: int) -> None:
        self.is_encrypted = False
        self.pages = [_FakePage(number) for number in range(1, page_count + 1)]


def _write_private(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    os.chmod(path.parent, 0o700)
    path.write_bytes(payload)
    os.chmod(path, 0o600)


def _simulate_group_readable_mode(monkeypatch: pytest.MonkeyPatch, target: Path) -> None:
    original_lstat = Path.lstat

    def patched_lstat(path: Path, *args: object, **kwargs: object) -> os.stat_result:
        result = original_lstat(path, *args, **kwargs)
        if path != target:
            return result
        values = list(result)
        values[0] |= stat.S_IRGRP
        return os.stat_result(values)

    monkeypatch.setattr(Path, "lstat", patched_lstat)


def _search_receipt() -> dict[str, object]:
    return {
        "schema_version": "phase3_university_source_negative_search_receipt_v1",
        "issue": intake.ISSUE,
        "wave": intake.WAVE,
        "preserved_candidate_count": 2,
        "preserved_source_ids": [intake.KOVALENKO_SOURCE_ID, intake.YASHNYK_SOURCE_ID],
        "phase_effect": {
            "topic_gaps_closed": 0,
            "topic_gaps_narrowed": False,
            "phase3_complete": False,
            "phase4_blocked": True,
        },
    }


def _acquisition_receipt(
    source_id: str,
    pdf_sha256: str,
    pdf_bytes: int,
    pdf_pages: int,
) -> dict[str, object]:
    return {
        "schema_version": "phase3_university_source_acquisition_receipt_v1",
        "status": "VERIFIED_DRIVE_CUSTODY_PENDING_QUALIFIED_SOURCE_DISPOSITION",
        "issue": intake.ISSUE,
        "wave": intake.WAVE,
        "source": {"source_id": source_id},
        "files": [
            {
                "role": "immutable_source_bytes",
                "sha256": pdf_sha256,
                "bytes": pdf_bytes,
            }
        ],
        "deterministic_inspection": {"pdf_pages": pdf_pages},
        "provisional_content_scope": {"qualified_ukrainian_source_review_state": "pending"},
        "rights_boundary": {
            "legal_reuse_authorization_established": False,
            "normative_rule_authority": False,
        },
        "gates": {
            "topic_gaps_closed": 0,
            "topic_gaps_narrowed": False,
            "phase3_complete": False,
            "phase4_blocked": True,
        },
    }


def _review_text() -> str:
    return (
        "topic_gaps_closed: 0\n"
        "topic_gaps_narrowed: true\n"
        "Kovalenko 2024 — PASS\n"
        "Yashnyk 2020 — PASS\n"
        "REJECT for any normative\n"
    )


def _fixture(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> dict[str, Path]:
    private = tmp_path / "private"
    schema_path = tmp_path / "schema.json"
    search_path = private / "search.json"
    k_pdf = private / "kovalenko.pdf"
    k_meta = private / "k-meta.html"
    k_acq = private / "k-acq.json"
    y_pdf = private / "yashnyk.pdf"
    y_meta = private / "y-meta.html"
    y_agreement = private / "y-agreement.txt"
    y_acq = private / "y-acq.json"
    review_path = private / "review.result"

    k_payload = b"kovalenko pdf bytes"
    y_payload = b"yashnyk pdf bytes"
    review_payload = _review_text().encode()

    monkeypatch.setattr(intake, "KOVALENKO_PDF_SHA256", hashlib.sha256(k_payload).hexdigest())
    monkeypatch.setattr(intake, "KOVALENKO_PDF_BYTES", len(k_payload))
    monkeypatch.setattr(intake, "YASHNYK_PDF_SHA256", hashlib.sha256(y_payload).hexdigest())
    monkeypatch.setattr(intake, "YASHNYK_PDF_BYTES", len(y_payload))
    monkeypatch.setattr(intake, "KOVALENKO_METADATA_SHA256", hashlib.sha256(b"k meta").hexdigest())
    monkeypatch.setattr(intake, "YASHNYK_METADATA_SHA256", hashlib.sha256(b"y meta").hexdigest())
    monkeypatch.setattr(intake, "YASHNYK_AUTHOR_AGREEMENT_SHA256", hashlib.sha256(b"y agree").hexdigest())
    monkeypatch.setattr(intake, "REVIEW_RESULT_SHA256", hashlib.sha256(review_payload).hexdigest())
    monkeypatch.setattr(intake, "REVIEW_RESULT_BYTES", len(review_payload))
    monkeypatch.setattr(intake, "SEARCH_RECEIPT_SHA256", intake.sha256_bytes(intake.canonical_bytes(_search_receipt())))
    monkeypatch.setattr(
        intake,
        "KOVALENKO_ACQUISITION_SHA256",
        intake.sha256_bytes(
            intake.canonical_bytes(
                _acquisition_receipt(
                    intake.KOVALENKO_SOURCE_ID,
                    intake.KOVALENKO_PDF_SHA256,
                    intake.KOVALENKO_PDF_BYTES,
                    intake.KOVALENKO_PAGES,
                )
            )
        ),
    )
    monkeypatch.setattr(
        intake,
        "YASHNYK_ACQUISITION_SHA256",
        intake.sha256_bytes(
            intake.canonical_bytes(
                _acquisition_receipt(
                    intake.YASHNYK_SOURCE_ID,
                    intake.YASHNYK_PDF_SHA256,
                    intake.YASHNYK_PDF_BYTES,
                    intake.YASHNYK_PAGES,
                )
            )
        ),
    )
    monkeypatch.setattr(
        intake,
        "PdfReader",
        lambda path: _FakeReader(intake.KOVALENKO_PAGES if "kovalenko" in str(path) else intake.YASHNYK_PAGES),
    )

    _write_private(search_path, intake.canonical_bytes(_search_receipt()))
    _write_private(k_pdf, k_payload)
    _write_private(k_meta, b"k meta")
    _write_private(
        k_acq,
        intake.canonical_bytes(
            _acquisition_receipt(
                intake.KOVALENKO_SOURCE_ID,
                intake.KOVALENKO_PDF_SHA256,
                intake.KOVALENKO_PDF_BYTES,
                intake.KOVALENKO_PAGES,
            )
        ),
    )
    _write_private(y_pdf, y_payload)
    _write_private(y_meta, b"y meta")
    _write_private(y_agreement, b"y agree")
    _write_private(
        y_acq,
        intake.canonical_bytes(
            _acquisition_receipt(
                intake.YASHNYK_SOURCE_ID,
                intake.YASHNYK_PDF_SHA256,
                intake.YASHNYK_PDF_BYTES,
                intake.YASHNYK_PAGES,
            )
        ),
    )
    _write_private(review_path, review_payload)
    schema_path.write_text('{"type":"object"}\n', encoding="utf-8")
    monkeypatch.setattr(intake, "SCHEMA_PATH", schema_path)

    return {
        "search": search_path,
        "k_pdf": k_pdf,
        "k_meta": k_meta,
        "k_acq": k_acq,
        "y_pdf": y_pdf,
        "y_meta": y_meta,
        "y_agreement": y_agreement,
        "y_acq": y_acq,
        "review": review_path,
    }


def _build(paths: dict[str, Path], custody_root: Path | None = None) -> dict[str, object]:
    return intake.build_receipt(
        search_receipt=paths["search"],
        kovalenko_pdf=paths["k_pdf"],
        kovalenko_metadata=paths["k_meta"],
        kovalenko_acquisition=paths["k_acq"],
        yashnyk_pdf=paths["y_pdf"],
        yashnyk_metadata=paths["y_meta"],
        yashnyk_author_agreement=paths["y_agreement"],
        yashnyk_acquisition=paths["y_acq"],
        review_result=paths["review"],
        write_drive_custody=custody_root,
    )


def _rehash(receipt: dict[str, object]) -> dict[str, object]:
    body = {key: value for key, value in receipt.items() if key != "receipt_sha256"}
    receipt["receipt_sha256"] = intake.sha256_bytes(intake.canonical_bytes(body))
    return receipt


def test_contract_schema_is_valid_and_text_free() -> None:
    schema_text = intake.SCHEMA_PATH.read_text(encoding="utf-8")
    Draft202012Validator.check_schema(json.loads(schema_text))
    assert '"source_text"' not in schema_text
    assert '"extracted_text"' not in schema_text
    assert "additionalProperties" in schema_text
    assert intake.STATUS in schema_text
    assert '"contextual_only"' in schema_text
    assert '"private_inspection_authorized"' not in schema_text
    assert '"producer_provider_calls"' in schema_text
    assert '"const": false' in schema_text or '"const":false' in schema_text.replace(" ", "")


def test_build_is_deterministic_and_fail_closed(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    paths = _fixture(tmp_path, monkeypatch)
    first = _build(paths)
    assert first == _build(paths)
    assert first["status"] == intake.STATUS
    assert first["producer_provider_calls"] is False  # type: ignore[index]
    assert first["review_provider_call_recorded"] is True  # type: ignore[index]
    assert first["review"]["topic_gaps_closed"] == 0  # type: ignore[index]
    assert first["review"]["topic_gaps_narrowed"] is True  # type: ignore[index]
    assert first["sources"][1]["normative_linguistic_rule_authority_rejected"] is True  # type: ignore[index]
    assert first["gates"]["phase4_blocked"] is True  # type: ignore[index]
    assert first["gates"]["phase3_complete"] is False  # type: ignore[index]


def test_pdf_byte_drift_is_rejected(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    paths = _fixture(tmp_path, monkeypatch)
    _write_private(paths["k_pdf"], b"changed")
    with pytest.raises(intake.WaveLModernPhoneticsReviewedIntakeError, match="byte drift"):
        _build(paths)


def test_search_provisional_narrowing_drift_is_rejected(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    paths = _fixture(tmp_path, monkeypatch)
    search = _search_receipt()
    search["phase_effect"]["topic_gaps_narrowed"] = True  # type: ignore[index]
    _write_private(paths["search"], intake.canonical_bytes(search))
    monkeypatch.setattr(intake, "SEARCH_RECEIPT_SHA256", intake.sha256_file(paths["search"]))
    with pytest.raises(intake.WaveLModernPhoneticsReviewedIntakeError, match="provisional narrowing drift"):
        _build(paths)


def test_acquisition_topic_closure_overclaim_is_rejected(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    paths = _fixture(tmp_path, monkeypatch)
    acq = json.loads(paths["k_acq"].read_text(encoding="utf-8"))
    acq["gates"]["topic_gaps_closed"] = 1
    _write_private(paths["k_acq"], intake.canonical_bytes(acq))
    monkeypatch.setattr(intake, "KOVALENKO_ACQUISITION_SHA256", intake.sha256_file(paths["k_acq"]))
    with pytest.raises(intake.WaveLModernPhoneticsReviewedIntakeError, match="overclaims topic closure"):
        _build(paths)


def test_rights_legal_reuse_overclaim_is_rejected(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    paths = _fixture(tmp_path, monkeypatch)
    receipt = _build(paths)
    receipt["rights"]["legal_reuse_authorization_established"] = True  # type: ignore[index]
    with pytest.raises(intake.WaveLModernPhoneticsReviewedIntakeError, match="legal reuse authorization"):
        intake.validate_receipt(_rehash(receipt))


def test_legacy_authorization_field_is_rejected(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    paths = _fixture(tmp_path, monkeypatch)
    receipt = _build(paths)
    receipt["rights"]["private_inspection_authorized"] = True  # type: ignore[index]
    with pytest.raises(intake.WaveLModernPhoneticsReviewedIntakeError, match="legacy authorization field"):
        intake.validate_receipt(_rehash(receipt))


def test_yashnyk_normative_authority_overclaim_is_rejected(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    paths = _fixture(tmp_path, monkeypatch)
    receipt = _build(paths)
    receipt["sources"][1]["normative_rule_authority"] = True  # type: ignore[index]
    with pytest.raises(intake.WaveLModernPhoneticsReviewedIntakeError, match="Yashnyk normative authority overclaim"):
        intake.validate_receipt(_rehash(receipt))


def test_v2_denominator_mutation_is_rejected(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    paths = _fixture(tmp_path, monkeypatch)
    receipt = _build(paths)
    receipt["gates"]["v2_denominator_mutated"] = True  # type: ignore[index]
    with pytest.raises(intake.WaveLModernPhoneticsReviewedIntakeError, match="mutates v2 denominator"):
        intake.validate_receipt(_rehash(receipt))


def test_private_input_modes_and_symlinks_are_rejected(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    paths = _fixture(tmp_path, monkeypatch)
    _simulate_group_readable_mode(monkeypatch, paths["k_pdf"])
    with pytest.raises(intake.WaveLModernPhoneticsReviewedIntakeError, match="mode 0600"):
        _build(paths)
    link = tmp_path / "k-link.pdf"
    link.symlink_to(paths["k_pdf"])
    paths["k_pdf"] = link
    with pytest.raises(intake.WaveLModernPhoneticsReviewedIntakeError, match="symbolic-link"):
        _build(paths)


def test_review_drive_custody_is_written(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    paths = _fixture(tmp_path, monkeypatch)
    custody_root = tmp_path / "wave-root"
    _build(paths, custody_root=custody_root)
    custody_dir = custody_root / intake.REVIEW_CUSTODY_SUBDIRECTORY
    review_dest = custody_dir / intake.REVIEW_RESULT_FILENAME
    receipt_path = custody_dir / intake.REVIEW_CUSTODY_RECEIPT_FILENAME
    sums_path = custody_dir / "SHA256SUMS"
    assert review_dest.is_file()
    assert receipt_path.is_file()
    assert sums_path.is_file()
    assert stat.S_IMODE(review_dest.stat().st_mode) == 0o600
    assert "acquisition_receipts_not_overwritten" in receipt_path.read_text(encoding="utf-8")


def test_public_receipt_is_immutable(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    paths = _fixture(tmp_path, monkeypatch)
    receipt = _build(paths)
    output = tmp_path / "public" / "receipt.json"
    monkeypatch.setattr(
        intake, "_inside_git_checkout", lambda path: output == Path(path) or output in Path(path).parents
    )
    intake.write_public_receipt(output, receipt)
    intake.write_public_receipt(output, receipt)
    output.write_text("{}\n", encoding="utf-8")
    with pytest.raises(intake.WaveLModernPhoneticsReviewedIntakeError, match="refusing to overwrite"):
        intake.write_public_receipt(output, receipt)


def test_tracked_receipt_validates_and_excludes_private_source_text() -> None:
    assert intake.DEFAULT_PUBLIC_RECEIPT_PATH.is_file(), "tracked receipt must exist in Git"
    receipt = json.loads(intake.DEFAULT_PUBLIC_RECEIPT_PATH.read_text(encoding="utf-8"))
    validated = intake.validate_receipt(receipt)
    assert validated["status"] == intake.STATUS
    serialized = intake.canonical_json(validated)
    assert "GoogleDrive-" not in serialized
    assert "@gmail.com" not in serialized
    assert "Барка" not in serialized
    assert validated["rights"]["legal_reuse_authorization_established"] is False
    assert validated["rights"]["operator_private_attributed_research_use_directed"] is True
