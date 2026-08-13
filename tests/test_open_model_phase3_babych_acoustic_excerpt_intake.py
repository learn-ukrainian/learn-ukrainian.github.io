from __future__ import annotations

import hashlib
import json
import os
import stat
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from scripts.projects.open_model_data import phase3_babych_acoustic_excerpt_intake as intake


class _FakePage:
    def __init__(self, text: str) -> None:
        self._text = text

    def extract_text(self) -> str:
        return self._text


class _FakeReader:
    def __init__(self, _path: Path, texts: list[str]) -> None:
        self.is_encrypted = False
        self.pages = [_FakePage(text) for text in texts]
        self.trailer = {"/Root": {}}

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


def _page_texts() -> list[str]:
    texts = [
        "Title page. Наталія Бабич",
        f"Copyright page. ISBN {intake.SOURCE_ISBN}. Київ : ТОВ «Альянт», 2022. — 294 с.",
        "Зміст",
        "Зміст continued",
        "5\nПЕРЕДМОВА",
        "6\nПередмова continued",
        "7\nПередмова continued",
        "8\nПередмова end",
        "20\nУМОВНІ ПОЗНАЧКИ",
        "21\nМОДУЛЬ І. початок",
        "22\nінтенсивність частота спектр тривалість фаза acoustic body",
        "23\nModule I continued",
        "Навчально-методичне видання\nПідписано до друку 27.07.2022 р.",
    ]
    assert len(texts) == intake.PDF_PAGES
    return texts


def _fixture(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> dict[str, Path]:
    private = tmp_path / "private"
    pdf_path = private / "source.pdf"
    mets_path = private / "mets.xml"
    item_path = private / "item.html"
    export_path = private / "export.json"
    schema_path = tmp_path / "schema.json"
    pdf_payload = b"fixture babych pdf bytes"
    texts = _page_texts()
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
        "page_manifest_sha256": hashlib.sha256(b"".join(intake.canonical_bytes(row) for row in page_rows)).hexdigest(),
        "extracted_text_sha256": hashlib.sha256("\n\f\n".join(texts).encode("utf-8")).hexdigest(),
    }
    monkeypatch.setattr(intake, "PDF_SHA256", hashlib.sha256(pdf_payload).hexdigest())
    monkeypatch.setattr(intake, "PDF_MD5", hashlib.md5(pdf_payload, usedforsecurity=False).hexdigest())
    monkeypatch.setattr(intake, "PDF_BYTES", len(pdf_payload))
    monkeypatch.setattr(intake, "PDF_PAGES", len(texts))
    monkeypatch.setattr(intake, "TEXT_BEARING_PAGES", len(texts))
    monkeypatch.setattr(intake, "UNICODE_CODE_POINTS", text_facts["unicode_code_points"])
    monkeypatch.setattr(intake, "UTF8_BYTES", text_facts["utf8_bytes"])
    monkeypatch.setattr(intake, "PAGE_MANIFEST_SHA256", text_facts["page_manifest_sha256"])
    monkeypatch.setattr(intake, "EXTRACTED_TEXT_SHA256", text_facts["extracted_text_sha256"])
    monkeypatch.setattr(intake, "PdfReader", lambda path: _FakeReader(path, texts))
    _write_private(pdf_path, pdf_payload)

    mets = f"""<?xml version="1.0" encoding="UTF-8"?>
<mets:mets xmlns:mets="http://www.loc.gov/METS/" xmlns:mods="http://www.loc.gov/mods/v3"
 xmlns:xlink="http://www.w3.org/1999/xlink" OBJID="{intake.SOURCE_METS_OBJID}" LABEL="Eprints Item">
  <mets:dmdSec><mets:mdWrap MDTYPE="MODS"><mets:xmlData>
    <mods:titleInfo><mods:title>{intake.SOURCE_METS_TITLE_CORRUPT}</mods:title></mods:titleInfo>
    <mods:name type="personal">
      <mods:namePart type="given">{intake.SOURCE_METADATA_GIVEN}</mods:namePart>
      <mods:namePart type="family">{intake.SOURCE_METADATA_FAMILY}</mods:namePart>
    </mods:name>
    <mods:originInfo><mods:dateIssued encoding="iso8601">2022</mods:dateIssued></mods:originInfo>
    <mods:originInfo><mods:publisher>{intake.SOURCE_PUBLISHER}</mods:publisher></mods:originInfo>
  </mets:xmlData></mets:mdWrap></mets:dmdSec>
  <mets:fileSec><mets:fileGrp>
    <mets:file ID="{intake.SOURCE_METS_FILE_ID}" SIZE="{len(pdf_payload)}"
      OWNERID="{intake.SOURCE_BITSTREAM_URL}" MIMETYPE="application/pdf">
      <mets:FLocat LOCTYPE="URL" xlink:type="simple" xlink:href="{intake.SOURCE_BITSTREAM_URL}" />
    </mets:file>
  </mets:fileGrp></mets:fileSec>
</mets:mets>
""".encode()
    item = f"""<!doctype html><html><head>
<meta name="DC.creator" content="{intake.SOURCE_METADATA_AUTHOR}" />
<meta name="eprints.creators_name" content="{intake.SOURCE_METADATA_AUTHOR}" />
<meta name="DC.title" content="{intake.SOURCE_TITLE}" />
<meta name="eprints.title" content="{intake.SOURCE_TITLE}" />
<meta name="DC.identifier" content="{intake.SOURCE_BITSTREAM_URL}" />
<meta name="eprints.document_url" content="{intake.SOURCE_BITSTREAM_URL}" />
<meta name="DC.relation" content="{intake.SOURCE_ITEM_URL}" />
<meta name="DC.date" content="2022" />
<meta name="eprints.isbn" content="{intake.SOURCE_ISBN}" />
<meta name="eprints.pages" content="294" />
</head><body>
<span class="person_name">{intake.SOURCE_AUTHOR_DISPLAY}</span>
<span class="person_name">{intake.SOURCE_METADATA_AUTHOR}</span>
</body></html>
""".encode()
    export = {
        "eprintid": int(intake.SOURCE_EPRINT_ID),
        "uri": intake.SOURCE_ITEM_URL_BARE,
        "date": 2022,
        "isbn": intake.SOURCE_ISBN,
        "pages": intake.CATALOG_PRINT_COLLATION_PAGES,
        "publisher": intake.SOURCE_PUBLISHER,
        "title": [{"lang": "uk", "text": intake.SOURCE_TITLE}],
        "creators": [
            {
                "id": "n.babych@kubg.edu.ua",
                "name": {
                    "given": intake.SOURCE_METADATA_GIVEN,
                    "family": intake.SOURCE_METADATA_FAMILY,
                },
            }
        ],
        "documents": [
            {
                "files": [
                    {
                        "filename": "N_Babych_FTFZOA_FPSRSO.pdf",
                        "filesize": len(pdf_payload),
                        "hash": intake.PDF_MD5,
                        "hash_type": "MD5",
                    }
                ]
            }
        ],
    }
    _write_private(mets_path, mets)
    _write_private(item_path, item)
    _write_private(export_path, intake.canonical_bytes(export))
    monkeypatch.setattr(intake, "METS_SHA256", intake.sha256_file(mets_path))
    monkeypatch.setattr(intake, "ITEM_RECORD_SHA256", intake.sha256_file(item_path))
    monkeypatch.setattr(intake, "EXPORT_JSON_SHA256", intake.sha256_file(export_path))
    schema_path.write_text('{"type":"object"}\n', encoding="utf-8")
    monkeypatch.setattr(intake, "SCHEMA_PATH", schema_path)
    return {
        "pdf": pdf_path,
        "mets": mets_path,
        "item": item_path,
        "export": export_path,
    }


def _build(paths: dict[str, Path]) -> dict[str, object]:
    return intake.build_receipt(
        source_pdf=paths["pdf"],
        mets=paths["mets"],
        item_record=paths["item"],
        export_json=paths["export"],
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
    assert '"topic_gaps_narrowed": []' in schema_text or '"topic_gaps_narrowed":[]' in schema_text.replace(" ", "")


def test_build_is_deterministic_and_fail_closed(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    paths = _fixture(tmp_path, monkeypatch)
    first = _build(paths)
    assert first == _build(paths)
    assert first["status"] == intake.STATUS
    assert first["review_scope"]["content_disposition"] == "contextual_only"  # type: ignore[index]
    assert first["review_scope"]["topic_gaps_closed"] == []  # type: ignore[index]
    assert first["review_scope"]["topic_gaps_narrowed"] == []  # type: ignore[index]
    assert first["review_scope"]["coverage_effect"] == "pending_ukrainian_source_review"  # type: ignore[index]
    assert first["source"]["exact_bitstream_pages"] == 13  # type: ignore[index]
    assert first["source"]["bitstream_is_complete_publication"] is False  # type: ignore[index]
    assert first["gates"]["phase4_blocked"] is True  # type: ignore[index]
    assert first["gates"]["phase3_complete"] is False  # type: ignore[index]
    assert first["gates"]["semantic_gold"] is False  # type: ignore[index]
    assert first["gates"]["training_conversion_complete"] is False  # type: ignore[index]


def test_pdf_byte_drift_is_rejected(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    paths = _fixture(tmp_path, monkeypatch)
    _write_private(paths["pdf"], b"changed")
    with pytest.raises(intake.BabychAcousticExcerptIntakeError, match="byte drift"):
        _build(paths)


def test_metadata_title_drift_is_rejected(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    paths = _fixture(tmp_path, monkeypatch)
    export = json.loads(paths["export"].read_text(encoding="utf-8"))
    export["title"] = [{"lang": "uk", "text": "Інша назва"}]
    _write_private(paths["export"], intake.canonical_bytes(export))
    monkeypatch.setattr(intake, "EXPORT_JSON_SHA256", intake.sha256_file(paths["export"]))
    with pytest.raises(intake.BabychAcousticExcerptIntakeError, match="title drift"):
        _build(paths)


def test_mets_objid_drift_is_rejected(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    paths = _fixture(tmp_path, monkeypatch)
    payload = (
        paths["mets"]
        .read_text(encoding="utf-8")
        .replace(
            f'OBJID="{intake.SOURCE_METS_OBJID}"',
            'OBJID="eprint_99999"',
        )
    )
    _write_private(paths["mets"], payload.encode())
    monkeypatch.setattr(intake, "METS_SHA256", intake.sha256_file(paths["mets"]))
    with pytest.raises(intake.BabychAcousticExcerptIntakeError, match="object identity drift"):
        _build(paths)


def test_mets_title_drift_is_rejected(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    paths = _fixture(tmp_path, monkeypatch)
    payload = (
        paths["mets"]
        .read_text(encoding="utf-8")
        .replace(
            intake.SOURCE_METS_TITLE_CORRUPT,
            "ARRAY(0xdeadbeef)",
        )
    )
    _write_private(paths["mets"], payload.encode())
    monkeypatch.setattr(intake, "METS_SHA256", intake.sha256_file(paths["mets"]))
    with pytest.raises(intake.BabychAcousticExcerptIntakeError, match="corrupt-title provenance drift"):
        _build(paths)


def test_mets_bitstream_drift_is_rejected(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    paths = _fixture(tmp_path, monkeypatch)
    drifted_url = intake.SOURCE_BITSTREAM_URL.replace("N_Babych", "N_Other")
    payload = paths["mets"].read_text(encoding="utf-8").replace(intake.SOURCE_BITSTREAM_URL, drifted_url)
    _write_private(paths["mets"], payload.encode())
    monkeypatch.setattr(intake, "METS_SHA256", intake.sha256_file(paths["mets"]))
    with pytest.raises(intake.BabychAcousticExcerptIntakeError, match="bitstream OWNERID drift"):
        _build(paths)


def test_html_identifier_drift_is_rejected(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    paths = _fixture(tmp_path, monkeypatch)
    drifted_url = intake.SOURCE_BITSTREAM_URL.replace("N_Babych", "N_Other")
    payload = paths["item"].read_text(encoding="utf-8").replace(intake.SOURCE_BITSTREAM_URL, drifted_url)
    _write_private(paths["item"], payload.encode())
    monkeypatch.setattr(intake, "ITEM_RECORD_SHA256", intake.sha256_file(paths["item"]))
    with pytest.raises(intake.BabychAcousticExcerptIntakeError, match="bitstream locator drift"):
        _build(paths)


def test_html_bitstream_drift_is_rejected(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    paths = _fixture(tmp_path, monkeypatch)
    drifted_url = intake.SOURCE_BITSTREAM_URL.replace("N_Babych", "N_Other")
    payload = (
        paths["item"]
        .read_text(encoding="utf-8")
        .replace(
            f'<meta name="eprints.document_url" content="{intake.SOURCE_BITSTREAM_URL}" />',
            f'<meta name="eprints.document_url" content="{drifted_url}" />',
        )
    )
    _write_private(paths["item"], payload.encode())
    monkeypatch.setattr(intake, "ITEM_RECORD_SHA256", intake.sha256_file(paths["item"]))
    with pytest.raises(intake.BabychAcousticExcerptIntakeError, match="eprints bitstream locator drift"):
        _build(paths)


def test_rights_legal_reuse_overclaim_is_rejected(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    paths = _fixture(tmp_path, monkeypatch)
    receipt = _build(paths)
    receipt["rights"]["legal_reuse_authorization_established"] = True  # type: ignore[index]
    with pytest.raises(intake.BabychAcousticExcerptIntakeError, match="legal reuse authorization"):
        intake.validate_receipt(_rehash(receipt))


def test_missing_acoustic_marker_is_rejected(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    paths = _fixture(tmp_path, monkeypatch)
    texts = _page_texts()
    texts[10] = "22\nModule body without required acoustic markers"
    monkeypatch.setattr(intake, "PdfReader", lambda path: _FakeReader(path, texts))
    with pytest.raises(intake.BabychAcousticExcerptIntakeError, match="acoustic marker missing"):
        _build(paths)


def test_prompt_binding_drift_is_rejected(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    paths = _fixture(tmp_path, monkeypatch)
    receipt = _build(paths)
    receipt["bindings"]["phase3_recovery_prompt_v2_sha256"] = "0" * 64  # type: ignore[index]
    with pytest.raises(intake.BabychAcousticExcerptIntakeError, match="v2 prompt binding drift"):
        intake.validate_receipt(_rehash(receipt))
    receipt = _build(paths)
    receipt["bindings"]["phase3_reboot_prompt_v3_sha256"] = "1" * 64  # type: ignore[index]
    with pytest.raises(intake.BabychAcousticExcerptIntakeError, match="v3 prompt binding drift"):
        intake.validate_receipt(_rehash(receipt))


def test_full_book_page_overclaim_is_rejected(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    paths = _fixture(tmp_path, monkeypatch)
    receipt = _build(paths)
    receipt["source"]["exact_bitstream_pages"] = 294  # type: ignore[index]
    with pytest.raises(intake.BabychAcousticExcerptIntakeError, match="page-count overclaim"):
        intake.validate_receipt(_rehash(receipt))
    receipt = _build(paths)
    receipt["source"]["bitstream_is_complete_publication"] = True  # type: ignore[index]
    with pytest.raises(intake.BabychAcousticExcerptIntakeError, match="full-book overclaim"):
        intake.validate_receipt(_rehash(receipt))


def test_print_page_discontinuity_drift_is_rejected(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    paths = _fixture(tmp_path, monkeypatch)
    texts = _page_texts()
    texts[8] = "19\nУМОВНІ ПОЗНАЧКИ"
    monkeypatch.setattr(intake, "PdfReader", lambda path: _FakeReader(path, texts))
    with pytest.raises(intake.BabychAcousticExcerptIntakeError, match="discontinuity drift"):
        _build(paths)


def test_missing_text_page_is_rejected(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    paths = _fixture(tmp_path, monkeypatch)
    texts = _page_texts()
    texts[3] = "   \n"
    monkeypatch.setattr(intake, "PdfReader", lambda path: _FakeReader(path, texts))
    with pytest.raises(intake.BabychAcousticExcerptIntakeError, match="no embedded text"):
        _build(paths)


def test_private_input_inside_git_is_rejected(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    paths = _fixture(tmp_path, monkeypatch)
    monkeypatch.setattr(intake, "_inside_git_checkout", lambda path: True)
    with pytest.raises(intake.BabychAcousticExcerptIntakeError, match="cannot live inside Git"):
        _build(paths)


def test_private_input_modes_and_symlinks_are_rejected(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    paths = _fixture(tmp_path, monkeypatch)
    _simulate_group_readable_mode(monkeypatch, paths["pdf"])
    with pytest.raises(intake.BabychAcousticExcerptIntakeError, match="mode 0600"):
        _build(paths)
    link = tmp_path / "source-link.pdf"
    link.symlink_to(paths["pdf"])
    paths["pdf"] = link
    with pytest.raises(intake.BabychAcousticExcerptIntakeError, match="symbolic-link"):
        _build(paths)


def test_parent_traversal_is_rejected_before_path_normalization(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    paths = _fixture(tmp_path, monkeypatch)
    paths["pdf"] = paths["pdf"].parent / ".." / paths["pdf"].parent.name / paths["pdf"].name
    with pytest.raises(intake.BabychAcousticExcerptIntakeError, match="parent traversal"):
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
    with pytest.raises(intake.BabychAcousticExcerptIntakeError, match="refusing to overwrite"):
        intake.write_public_receipt(output, receipt)


def test_concurrent_receipt_creation_cannot_clobber_winner(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    paths = _fixture(tmp_path, monkeypatch)
    receipt = _build(paths)
    output = tmp_path / "public" / "receipt.json"
    monkeypatch.setattr(
        intake, "_inside_git_checkout", lambda path: output == Path(path) or output in Path(path).parents
    )

    def concurrent_link(source: Path, destination: Path, *, follow_symlinks: bool) -> None:
        output.write_text("{}\n", encoding="utf-8")
        raise FileExistsError

    monkeypatch.setattr(os, "link", concurrent_link)
    with pytest.raises(intake.BabychAcousticExcerptIntakeError, match="refusing to overwrite"):
        intake.write_public_receipt(output, receipt)
    assert output.read_text(encoding="utf-8") == "{}\n"


def test_receipt_self_hash_and_schema_overclaims_are_rejected(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    paths = _fixture(tmp_path, monkeypatch)
    receipt = _build(paths)
    receipt["receipt_sha256"] = "0" * 64
    with pytest.raises(intake.BabychAcousticExcerptIntakeError, match="self-hash drift"):
        intake.validate_receipt(receipt)
    receipt = _build(paths)
    receipt["review_scope"]["topic_gaps_narrowed"] = ["phonetics"]  # type: ignore[index]
    with pytest.raises(intake.BabychAcousticExcerptIntakeError, match="topic narrowing"):
        intake.validate_receipt(_rehash(receipt))
    receipt = _build(paths)
    receipt["gates"]["semantic_gold"] = True  # type: ignore[index]
    with pytest.raises(intake.BabychAcousticExcerptIntakeError, match="semantic_gold"):
        intake.validate_receipt(_rehash(receipt))


def test_tracked_receipt_validates_and_excludes_private_source_text() -> None:
    assert intake.DEFAULT_PUBLIC_RECEIPT_PATH.is_file(), "tracked receipt must exist in Git"
    receipt = json.loads(intake.DEFAULT_PUBLIC_RECEIPT_PATH.read_text(encoding="utf-8"))
    validated = intake.validate_receipt(receipt)
    assert validated["status"] == intake.STATUS
    serialized = intake.canonical_json(validated)
    assert "GoogleDrive-" not in serialized
    assert "@gmail.com" not in serialized
    assert "децибел" not in serialized
    assert "ФОНЕТИКА ТА ФОНОЛОГІЯ" not in serialized
    assert "інтенсивність" not in serialized
    assert validated["rights"]["legal_reuse_authorization_established"] is False
    assert validated["rights"]["operator_private_attributed_research_use_directed"] is True
