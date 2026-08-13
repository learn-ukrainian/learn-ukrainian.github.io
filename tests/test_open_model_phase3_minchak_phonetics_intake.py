from __future__ import annotations

import hashlib
import json
import os
import stat
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from scripts.projects.open_model_data import phase3_minchak_phonetics_intake as intake


class _FakePage:
    def __init__(self, text: str) -> None:
        self._text = text

    def extract_text(self) -> str:
        return self._text


class _FakeReader:
    def __init__(self, _path: Path, texts: list[str]) -> None:
        self.is_encrypted = False
        self.pages = [_FakePage(text) for text in texts]
        self.trailer = {"/Root": {"/AcroForm": {}}}

    def get_fields(self) -> dict[str, object]:
        return {}


def _write_private(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    os.chmod(path.parent, 0o700)
    path.write_bytes(payload)
    os.chmod(path, 0o600)


def _simulate_group_readable_mode(
    monkeypatch: pytest.MonkeyPatch,
    target: Path,
) -> None:
    original_lstat = Path.lstat

    def patched_lstat(path: Path, *args: object, **kwargs: object) -> os.stat_result:
        result = original_lstat(path, *args, **kwargs)
        if path != target:
            return result
        values = list(result)
        values[0] |= stat.S_IRGRP
        return os.stat_result(values)

    monkeypatch.setattr(Path, "lstat", patched_lstat)


def _fixture(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> dict[str, Path]:
    private = tmp_path / "private"
    pdf_path = private / "source.pdf"
    mets_path = private / "mets.xml"
    item_path = private / "item.html"
    publications_path = private / "publications.html"
    review_path = private / "review.json"
    schema_path = tmp_path / "schema.json"
    pdf_payload = b"fixture pdf bytes"
    texts = [f"Перша сторінка. ISBN {intake.SOURCE_ISBN}. Київ, 2023. 131 с.", "2"]
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
        "unicode_code_points": sum(len(text) for text in texts),
        "utf8_bytes": sum(len(text.encode("utf-8")) for text in texts),
        "page_manifest_sha256": hashlib.sha256(
            b"".join(intake.canonical_bytes(row) for row in page_rows)
        ).hexdigest(),
        "extracted_text_sha256": hashlib.sha256("\n\f\n".join(texts).encode("utf-8")).hexdigest(),
    }
    monkeypatch.setattr(intake, "PDF_SHA256", hashlib.sha256(pdf_payload).hexdigest())
    monkeypatch.setattr(intake, "PDF_MD5", hashlib.md5(pdf_payload, usedforsecurity=False).hexdigest())
    monkeypatch.setattr(intake, "PDF_BYTES", len(pdf_payload))
    monkeypatch.setattr(intake, "PDF_PAGES", len(texts))
    monkeypatch.setattr(intake, "TEXT_BEARING_PAGES", len(texts))
    monkeypatch.setattr(intake, "SUBSTANTIVE_PAGES", 1)
    monkeypatch.setattr(intake, "INTENTIONAL_BLANK_PAGES", [2])
    monkeypatch.setattr(intake, "UNICODE_CODE_POINTS", text_facts["unicode_code_points"])
    monkeypatch.setattr(intake, "UTF8_BYTES", text_facts["utf8_bytes"])
    monkeypatch.setattr(intake, "PAGE_MANIFEST_SHA256", text_facts["page_manifest_sha256"])
    monkeypatch.setattr(intake, "EXTRACTED_TEXT_SHA256", text_facts["extracted_text_sha256"])
    monkeypatch.setattr(intake, "PdfReader", lambda path: _FakeReader(path, texts))
    _write_private(pdf_path, pdf_payload)

    mets = f"""<?xml version="1.0" encoding="UTF-8"?>
<mets:mets xmlns:mets="http://www.loc.gov/METS/" xmlns:dim="http://www.dspace.org/xmlns/dspace/dim"
 ID="hdl:{intake.SOURCE_HANDLE}" OBJEDIT="info:fedora/{intake.SOURCE_METS_ITEM_UUID}">
  <mets:dmdSec><mets:mdWrap><mets:xmlData><dim:dim>
    <dim:field element="contributor" qualifier="author">{intake.SOURCE_METADATA_AUTHOR}</dim:field>
    <dim:field element="date" qualifier="issued">2023</dim:field>
    <dim:field element="identifier" qualifier="uri">{intake.SOURCE_ITEM_URL}</dim:field>
    <dim:field element="title">{intake.SOURCE_TITLE}</dim:field>
    <dim:field element="type">Book</dim:field>
    <dim:field element="publisher">{intake.SOURCE_CATALOG_CITATION}</dim:field>
  </dim:dim></mets:xmlData></mets:mdWrap></mets:dmdSec>
  <mets:fileSec><mets:fileGrp><mets:file ID="file_{intake.SOURCE_METS_FILE_UUID}"
    SIZE="{len(pdf_payload)}" CHECKSUMTYPE="MD5" CHECKSUM="{intake.PDF_MD5}">
    <mets:FLocat xmlns:xlink="http://www.w3.org/TR/xlink/" xlink:href="{intake.SOURCE_BITSTREAM_PATH.replace('&', '&amp;')}" />
  </mets:file></mets:fileGrp></mets:fileSec>
</mets:mets>
""".encode()
    item = f"""<!doctype html><html><head>
<meta content="{intake.SOURCE_METADATA_AUTHOR}" name="DC.creator" />
<meta name="DC.title" xml:lang="uk" content="{intake.SOURCE_TITLE}" />
<meta content="{intake.SOURCE_ITEM_URL}" name="DC.identifier" />
<meta content="2023" name="citation_date" />
<meta content="{intake.SOURCE_CATALOG_CITATION}" name="DC.publisher" />
</head></html>
""".encode()
    publications = f"<a href=\"/{intake.SOURCE_HANDLE}\">{intake.SOURCE_TITLE}</a>\n".encode()
    _write_private(mets_path, mets)
    _write_private(item_path, item)
    _write_private(publications_path, publications)
    monkeypatch.setattr(intake, "METS_SHA256", intake.sha256_file(mets_path))
    monkeypatch.setattr(intake, "ITEM_RECORD_SHA256", intake.sha256_file(item_path))
    monkeypatch.setattr(intake, "PUBLICATIONS_PAGE_SHA256", intake.sha256_file(publications_path))
    schema_path.write_text('{"type":"object"}\n', encoding="utf-8")
    monkeypatch.setattr(intake, "SCHEMA_PATH", schema_path)

    bindings = {
        "all_bound_hashes_matched": True,
        "input_drift": "none",
        "pdf_sha256": intake.PDF_SHA256,
        "pdf_md5": intake.PDF_MD5,
        "pdf_bytes": intake.PDF_BYTES,
        "pdf_pages_actual": intake.PDF_PAGES,
        "pages_with_embedded_text": intake.TEXT_BEARING_PAGES,
        "substantive_pages": intake.SUBSTANTIVE_PAGES,
        "mets_sha256": intake.METS_SHA256,
        "item_record_sha256": intake.ITEM_RECORD_SHA256,
        "publications_page_sha256": intake.PUBLICATIONS_PAGE_SHA256,
        "phase3_reboot_prompt_v3_sha256": intake.V3_PROMPT_SHA256,
    }
    review = {
        "schema_version": "phase3_minchak_knlu_source_fitness_review_v1",
        "reviewer_identity": {
            "seat": "Ukrainian Source Reviewer",
            "model_x_harness": "claude/claude-fable-5 via native Claude CLI",
            "read_only": True,
        },
        "source_id": intake.SOURCE_ID,
        "input_bindings_verified": bindings,
        "recommended_disposition": "admit_scoped_candidate",
        "topic_gaps_closed": [],
        "closure_candidates_pending_matrix_critic": [{"area": "phonology"}],
        "topic_gate_effect": {
            "phonology": "closure_candidate_pending_matrix_critic",
            **{topic: "narrows_only" for topic in intake.TOPICS_NARROWED},
        },
        "retained_extracted_text_authorized": False,
        "private_training_conversion_candidate": True,
        "public_redistribution_authorized": False,
        "normative_rule_authority": False,
        "semantic_gold": False,
        "source_universe_freeze_authorized": False,
        "database_ingest_authorized": False,
        "phase3_complete": False,
        "phase4_blocked": True,
    }
    _write_private(review_path, intake.canonical_bytes(review))
    monkeypatch.setattr(intake, "REVIEW_RESULT_SHA256", intake.sha256_file(review_path))
    return {
        "pdf": pdf_path,
        "mets": mets_path,
        "item": item_path,
        "publications": publications_path,
        "review": review_path,
    }


def _build(paths: dict[str, Path]) -> dict[str, object]:
    return intake.build_receipt(
        source_pdf=paths["pdf"],
        mets=paths["mets"],
        item_record=paths["item"],
        publications_page=paths["publications"],
        review_result=paths["review"],
    )


def test_contract_schema_is_valid_and_text_free() -> None:
    schema_text = intake.SCHEMA_PATH.read_text(encoding="utf-8")
    Draft202012Validator.check_schema(json.loads(schema_text))
    assert '"source_text"' not in schema_text
    assert '"extracted_text"' not in schema_text


def test_build_is_deterministic_and_fail_closed(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    paths = _fixture(tmp_path, monkeypatch)
    first = _build(paths)
    assert first == _build(paths)
    assert first["review"]["topic_gaps_closed"] == []  # type: ignore[index]
    assert first["review"]["closure_candidates_pending_matrix_critic"] == ["phonology"]  # type: ignore[index]
    assert first["gates"]["source_coverage_ready"] is False  # type: ignore[index]
    assert first["gates"]["phase3_complete"] is False  # type: ignore[index]
    assert first["gates"]["phase4_blocked"] is True  # type: ignore[index]


def test_pdf_byte_drift_is_rejected(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    paths = _fixture(tmp_path, monkeypatch)
    _write_private(paths["pdf"], b"changed")
    with pytest.raises(intake.MinchakPhoneticsIntakeError, match="byte drift"):
        _build(paths)


def test_unbound_pdf_catalog_claim_is_rejected(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    paths = _fixture(tmp_path, monkeypatch)
    monkeypatch.setattr(intake, "PdfReader", lambda path: _FakeReader(path, ["Перша сторінка.", "2"]))
    with pytest.raises(intake.MinchakPhoneticsIntakeError, match="ISBN drift"):
        _build(paths)


def test_unexpected_blank_page_is_rejected(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    paths = _fixture(tmp_path, monkeypatch)
    first_page = f"Перша сторінка. ISBN {intake.SOURCE_ISBN}. Київ, 2023. 131 с."
    monkeypatch.setattr(intake, "PdfReader", lambda path: _FakeReader(path, [first_page, "Друга"]))
    with pytest.raises(intake.MinchakPhoneticsIntakeError, match="text-layer facts drift"):
        _build(paths)


def test_mets_identity_drift_is_rejected(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    paths = _fixture(tmp_path, monkeypatch)
    payload = paths["mets"].read_text(encoding="utf-8").replace(intake.SOURCE_METADATA_AUTHOR, "Інший автор")
    _write_private(paths["mets"], payload.encode())
    monkeypatch.setattr(intake, "METS_SHA256", intake.sha256_file(paths["mets"]))
    with pytest.raises(intake.MinchakPhoneticsIntakeError, match="author drift"):
        _build(paths)


def test_html_meta_attribute_order_is_irrelevant(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    paths = _fixture(tmp_path, monkeypatch)
    assert _build(paths)["source"]["source_id"] == intake.SOURCE_ID  # type: ignore[index]


@pytest.mark.parametrize(
    ("field", "value", "match"),
    [
        ("topic_gaps_closed", ["phonology"], "closed topic gap"),
        ("normative_rule_authority", True, "normative_rule_authority"),
        ("semantic_gold", True, "semantic_gold"),
        ("database_ingest_authorized", True, "database_ingest_authorized"),
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
    with pytest.raises(intake.MinchakPhoneticsIntakeError, match=match):
        _build(paths)


def test_private_input_modes_and_symlinks_are_rejected(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    paths = _fixture(tmp_path, monkeypatch)
    _simulate_group_readable_mode(monkeypatch, paths["pdf"])
    with pytest.raises(intake.MinchakPhoneticsIntakeError, match="mode 0600"):
        _build(paths)
    link = tmp_path / "source-link.pdf"
    link.symlink_to(paths["pdf"])
    paths["pdf"] = link
    with pytest.raises(intake.MinchakPhoneticsIntakeError, match="symbolic-link"):
        _build(paths)


def test_parent_traversal_is_rejected_before_path_normalization(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    paths = _fixture(tmp_path, monkeypatch)
    paths["pdf"] = paths["pdf"].parent / ".." / paths["pdf"].parent.name / paths["pdf"].name
    with pytest.raises(intake.MinchakPhoneticsIntakeError, match="parent traversal"):
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
    with pytest.raises(intake.MinchakPhoneticsIntakeError, match="refusing to overwrite"):
        intake.write_public_receipt(output, receipt)


def test_concurrent_receipt_creation_cannot_clobber_winner(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    paths = _fixture(tmp_path, monkeypatch)
    receipt = _build(paths)
    output = tmp_path / "public" / "receipt.json"
    monkeypatch.setattr(
        intake, "_inside_git_checkout", lambda path: output == Path(path) or output in Path(path).parents
    )
    original_link = os.link

    def concurrent_link(source: Path, destination: Path, *, follow_symlinks: bool) -> None:
        output.write_text("{}\n", encoding="utf-8")
        raise FileExistsError

    monkeypatch.setattr(os, "link", concurrent_link)
    with pytest.raises(intake.MinchakPhoneticsIntakeError, match="refusing to overwrite"):
        intake.write_public_receipt(output, receipt)
    assert output.read_text(encoding="utf-8") == "{}\n"
    monkeypatch.setattr(os, "link", original_link)


def test_receipt_self_hash_and_runtime_bindings_are_enforced(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    paths = _fixture(tmp_path, monkeypatch)
    receipt = _build(paths)
    receipt["receipt_sha256"] = "0" * 64
    with pytest.raises(intake.MinchakPhoneticsIntakeError, match="self-hash drift"):
        intake.validate_receipt(receipt)


def test_tracked_receipt_validates_when_present() -> None:
    if not intake.DEFAULT_PUBLIC_RECEIPT_PATH.exists():
        pytest.skip("tracked receipt is generated after the implementation stabilizes")
    receipt = json.loads(intake.DEFAULT_PUBLIC_RECEIPT_PATH.read_text(encoding="utf-8"))
    assert intake.validate_receipt(receipt)["status"] == intake.STATUS
