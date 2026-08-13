from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from scripts.projects.open_model_data import phase3_vspu_modern_theory_intake as intake


class _FakePage:
    def __init__(self, text: str) -> None:
        self._text = text

    def extract_text(self) -> str:
        return self._text


class _FakeReader:
    def __init__(self, _path: Path, texts: list[str]) -> None:
        self.is_encrypted = False
        self.pages = [_FakePage(text) for text in texts]


def _write_private(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    os.chmod(path.parent, 0o700)
    path.write_bytes(payload)
    os.chmod(path, 0o600)


def _fixture(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> dict[str, Path]:
    pdf_path = tmp_path / "private" / "source.pdf"
    item_path = tmp_path / "private" / "item.json"
    bitstream_path = tmp_path / "private" / "bitstream.json"
    review_path = tmp_path / "private" / "review.json"
    schema_path = tmp_path / "schema.json"
    pdf_payload = b"fixture pdf bytes"
    texts = ["Перша сторінка українського джерела.", "Друга сторінка з теорією."]
    page_rows = []
    for page_number, text in enumerate(texts, start=1):
        encoded = text.encode("utf-8")
        page_rows.append(
            {
                "page": page_number,
                "chars": len(text),
                "bytes": len(encoded),
                "sha256": hashlib.sha256(encoded).hexdigest(),
            }
        )
    text_facts = {
        "pages": len(texts),
        "text_bearing_pages": len(texts),
        "unicode_code_points": sum(len(text) for text in texts),
        "utf8_bytes": sum(len(text.encode("utf-8")) for text in texts),
        "page_manifest_sha256": hashlib.sha256(b"".join(intake.canonical_bytes(row) for row in page_rows)).hexdigest(),
        "extracted_text_sha256": hashlib.sha256("\n\f\n".join(texts).encode("utf-8")).hexdigest(),
    }
    item = {
        "uuid": intake.SOURCE_ITEM_UUID,
        "name": intake.SOURCE_TITLE.upper(),
        "metadata": {
            "dc.date.issued": [{"value": "2021"}],
            "dc.identifier.isbn": [{"value": intake.SOURCE_ISBN}],
            "dc.identifier.uri": [{"value": intake.SOURCE_ITEM_URL}],
            "dc.contributor.author": [{"value": author} for author in intake.SOURCE_METADATA_AUTHORS],
            "dc.rights": [],
        },
    }
    bitstream = {
        "uuid": intake.SOURCE_BITSTREAM_UUID,
        "sizeBytes": len(pdf_payload),
        "bundleName": "ORIGINAL",
        "checkSum": {
            "checkSumAlgorithm": "MD5",
            "value": hashlib.md5(pdf_payload, usedforsecurity=False).hexdigest(),
        },
    }
    _write_private(pdf_path, pdf_payload)
    _write_private(item_path, intake.canonical_bytes(item))
    _write_private(bitstream_path, intake.canonical_bytes(bitstream))
    monkeypatch.setattr(intake, "PDF_SHA256", hashlib.sha256(pdf_payload).hexdigest())
    monkeypatch.setattr(intake, "PDF_MD5", hashlib.md5(pdf_payload, usedforsecurity=False).hexdigest())
    monkeypatch.setattr(intake, "PDF_BYTES", len(pdf_payload))
    monkeypatch.setattr(intake, "PDF_PAGES", len(texts))
    monkeypatch.setattr(intake, "TEXT_BEARING_PAGES", len(texts))
    monkeypatch.setattr(intake, "UNICODE_CODE_POINTS", text_facts["unicode_code_points"])
    monkeypatch.setattr(intake, "UTF8_BYTES", text_facts["utf8_bytes"])
    monkeypatch.setattr(intake, "PAGE_MANIFEST_SHA256", text_facts["page_manifest_sha256"])
    monkeypatch.setattr(intake, "EXTRACTED_TEXT_SHA256", text_facts["extracted_text_sha256"])
    monkeypatch.setattr(intake, "ITEM_METADATA_SHA256", intake.sha256_file(item_path))
    monkeypatch.setattr(intake, "BITSTREAM_METADATA_SHA256", intake.sha256_file(bitstream_path))
    monkeypatch.setattr(intake, "PdfReader", lambda path: _FakeReader(path, texts))
    schema_path.write_text('{"type":"object"}\n', encoding="utf-8")
    monkeypatch.setattr(intake, "SCHEMA_PATH", schema_path)
    review = {
        "schema_version": "phase3_vspu_modern_theory_source_review_v1",
        "reviewer_seat": "Ukrainian Source Reviewer",
        "retry_scope": "hash_blocker_resolution_only_no_semantic_rerun",
        "source_id": intake.SOURCE_ID,
        "verified_bindings": {
            "pdf_sha256": intake.PDF_SHA256,
            "pdf_bytes": intake.PDF_BYTES,
            **text_facts,
            "item_metadata_sha256": intake.ITEM_METADATA_SHA256,
            "bitstream_metadata_sha256": intake.BITSTREAM_METADATA_SHA256,
        },
        "prior_review_denominator": {
            "pages_total": len(texts),
            "pages_inspected": len(texts),
            "coverage": "all_pages_inspected",
            "source_type": "vspu_native_audience_bachelor_handbook_2021",
            "content_fit": "ukrainian_canon_broad_encyclopedic_theory_plus_worked_analysis_samples",
        },
        "content_disposition": "admit_scoped_candidate",
        "topic_gaps_closed": [],
        "topic_gaps_narrowed": intake.TOPICS_NARROWED,
        "topic_gaps_unchanged": intake.TOPICS_UNCHANGED,
        "primary_roles": intake.PRIMARY_ROLES,
        "secondary_roles": intake.SECONDARY_ROLES,
        "rights_state": {
            "standardized_license": "none",
            "authorization": "operator_explicit_private_text_only_phase3_use",
            "conditions": ["attribution", "truthful_no_license_statement", "takedown_readiness"],
        },
        "allowed_lanes": intake.ALLOWED_LANES,
        "prohibited_claims": intake.PROHIBITED_CLAIMS,
        "normative_rule_authority": False,
        "database_ingest_authorized": False,
        "training_conversion_complete": False,
        "semantic_gold": False,
        "source_universe_frozen": False,
        "phase3_complete": False,
        "phase4_blocked": True,
        "verdict": intake.STATUS,
    }
    _write_private(review_path, intake.canonical_bytes(review))
    monkeypatch.setattr(intake, "REVIEW_RESULT_SHA256", intake.sha256_file(review_path))
    return {
        "pdf": pdf_path,
        "item": item_path,
        "bitstream": bitstream_path,
        "review": review_path,
        "schema": schema_path,
    }


def _build(paths: dict[str, Path]) -> dict[str, object]:
    return intake.build_receipt(
        source_pdf=paths["pdf"],
        item_metadata=paths["item"],
        bitstream_metadata=paths["bitstream"],
        review_result=paths["review"],
    )


def test_contract_schema_is_valid_and_text_free() -> None:
    schema = json.loads(intake.SCHEMA_PATH.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    assert '"source_text"' not in intake.SCHEMA_PATH.read_text(encoding="utf-8")


def test_build_is_deterministic_and_fail_closed(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    paths = _fixture(tmp_path, monkeypatch)
    first = _build(paths)
    second = _build(paths)
    assert first == second
    assert first["review"]["topic_gaps_closed"] == []  # type: ignore[index]
    assert len(first["review"]["topic_gaps_narrowed"]) == 10  # type: ignore[index]
    assert first["gates"]["phase3_complete"] is False  # type: ignore[index]
    assert first["gates"]["phase4_blocked"] is True  # type: ignore[index]


def test_pdf_byte_drift_is_rejected(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    paths = _fixture(tmp_path, monkeypatch)
    paths["pdf"].write_bytes(b"changed")
    os.chmod(paths["pdf"], 0o600)
    with pytest.raises(intake.VspuModernTheoryIntakeError, match=r"byte denominator drift|SHA-256 drift"):
        _build(paths)


def test_missing_page_text_is_rejected(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    paths = _fixture(tmp_path, monkeypatch)
    monkeypatch.setattr(intake, "PdfReader", lambda path: _FakeReader(path, ["Перша", ""]))
    with pytest.raises(intake.VspuModernTheoryIntakeError, match="has no embedded text"):
        _build(paths)


def test_metadata_identity_drift_is_rejected(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    paths = _fixture(tmp_path, monkeypatch)
    item = json.loads(paths["item"].read_text(encoding="utf-8"))
    item["uuid"] = "wrong"
    _write_private(paths["item"], intake.canonical_bytes(item))
    monkeypatch.setattr(intake, "ITEM_METADATA_SHA256", intake.sha256_file(paths["item"]))
    with pytest.raises(intake.VspuModernTheoryIntakeError, match="item UUID drift"):
        _build(paths)


@pytest.mark.parametrize(
    ("field", "value", "match"),
    [
        ("topic_gaps_closed", ["phonetics"], "closed topic gap"),
        ("normative_rule_authority", True, "source-wide normative authority"),
        ("semantic_gold", True, "semantic_gold"),
        ("phase3_complete", True, "phase3_complete"),
        ("phase4_blocked", False, "opens Phase 4"),
    ],
)
def test_review_overclaims_are_rejected(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    field: str,
    value: object,
    match: str,
) -> None:
    paths = _fixture(tmp_path, monkeypatch)
    review = json.loads(paths["review"].read_text(encoding="utf-8"))
    review[field] = value
    _write_private(paths["review"], intake.canonical_bytes(review))
    monkeypatch.setattr(intake, "REVIEW_RESULT_SHA256", intake.sha256_file(paths["review"]))
    with pytest.raises(intake.VspuModernTheoryIntakeError, match=match):
        _build(paths)


def test_private_input_modes_and_symlinks_are_rejected(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    paths = _fixture(tmp_path, monkeypatch)
    os.chmod(paths["pdf"], 0o640)
    with pytest.raises(intake.VspuModernTheoryIntakeError, match="mode 0600"):
        _build(paths)
    os.chmod(paths["pdf"], 0o600)
    link = tmp_path / "source-link.pdf"
    link.symlink_to(paths["pdf"])
    paths["pdf"] = link
    with pytest.raises(intake.VspuModernTheoryIntakeError, match="symbolic-link"):
        _build(paths)


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
    with pytest.raises(intake.VspuModernTheoryIntakeError, match="refusing to overwrite"):
        intake.write_public_receipt(output, receipt)


def test_receipt_self_hash_and_runtime_bindings_are_enforced(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    paths = _fixture(tmp_path, monkeypatch)
    receipt = _build(paths)
    receipt["receipt_sha256"] = "0" * 64
    with pytest.raises(intake.VspuModernTheoryIntakeError, match="self-hash drift"):
        intake.validate_receipt(receipt)


def test_tracked_receipt_validates_when_present() -> None:
    if not intake.DEFAULT_PUBLIC_RECEIPT_PATH.exists():
        pytest.skip("tracked receipt is generated after the implementation stabilizes")
    receipt = json.loads(intake.DEFAULT_PUBLIC_RECEIPT_PATH.read_text(encoding="utf-8"))
    assert intake.validate_receipt(receipt)["status"] == intake.STATUS
