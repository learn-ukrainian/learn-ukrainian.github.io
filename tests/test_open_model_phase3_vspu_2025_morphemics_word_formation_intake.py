"""Hermetic tests for VSPU 2025 morphemics/word-formation source admission."""

from __future__ import annotations

import copy
import hashlib
import json
import os
import stat
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from scripts.projects.open_model_data import phase3_vspu_2025_morphemics_word_formation_intake as intake

PUBLIC_RECEIPT = intake.DEFAULT_PUBLIC_RECEIPT_PATH
SCHEMA = intake.SCHEMA_PATH


def _drive_staging() -> Path | None:
    try:
        return intake.default_staging_root()
    except intake.Vspu2025MorphemicsWordFormationIntakeError:
        return None


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


def _page_texts() -> list[str]:
    return [
        (
            "Титул. Морфеміка морфемний морфема. Словотвір дериват словотвор. "
            "DOI 10.31652/811.161.2-2025-1-198. Бакалавр філолог. "
            "Рекомендовано вченою радою. Вінницький державний педагогічний університет. "
            "© Ольга Павлушенко, 2025"
        ),
        "семантика визначення класифікація наприклад завдання походження історичн",
        "фразеологія типолог практичн вправ словник лексикограф лексиколог",
        "полісемі омонім синонім антонім значення слова дефініц давньорус",
        "російськ радянськ етимолог язик морфемік словотвір",
    ]


def _landing_html() -> str:
    return (
        "<html><head><title>item</title></head><body>"
        f"<h1>{intake.SOURCE_TITLE}</h1>"
        f"<p>DOI {intake.SOURCE_DOI}</p>"
        f"<p>uuid {intake.SOURCE_ITEM_UUID}</p>"
        "<span>Creative Commons</span>"
        "</body></html>\n"
    )


def _item_metadata() -> dict[str, object]:
    return {
        "id": intake.SOURCE_ITEM_UUID,
        "metadata": {
            "dc.title": [{"value": intake.SOURCE_TITLE}],
            "dc.contributor.author": [{"value": intake.SOURCE_METADATA_AUTHORS[0]}],
            "dc.date.issued": [{"value": "2025"}],
            "dc.publisher": [{"value": intake.SOURCE_PUBLISHER}],
            "dc.type": [{"value": "Book"}],
            "dc.identifier.doi": [{"value": f"https://doi.org/{intake.SOURCE_DOI}"}],
            "dc.identifier.citation": [
                {
                    "value": (
                        "Павлушенко О. А. Українська мова... Вінниця : Docuprint, 2025. 198 с. "
                        f"DOI: https://doi.org/{intake.SOURCE_DOI}"
                    )
                }
            ],
        },
    }


def _bitstream_metadata() -> dict[str, object]:
    return {
        "id": intake.SOURCE_BITSTREAM_UUID,
        "sizeBytes": 0,  # patched via monkeypatch PDF_BYTES after write
        "checkSum": {"checkSumAlgorithm": "MD5", "value": "pending"},
    }


def _content_fit_from_texts(texts: list[str]) -> dict[str, object]:
    joined_lower = "\n".join(texts).lower()
    joined = "\n".join(texts)
    normalized = " ".join(joined.split())
    hits = {
        key: sum(joined_lower.count(marker) for marker in markers)
        for key, markers in intake.CONTENT_FIT_MARKERS.items()
    }
    page_counts = {
        "morphemics_topic_pages": sum(
            1 for text in texts if any(marker in text.lower() for marker in intake.CONTENT_FIT_MARKERS["morphemics"])
        ),
        "word_formation_topic_pages": sum(
            1
            for text in texts
            if any(marker in text.lower() for marker in intake.CONTENT_FIT_MARKERS["word_formation"])
        ),
        "semantics_topic_pages": sum(
            1 for text in texts if any(marker in text.lower() for marker in intake.CONTENT_FIT_MARKERS["semantics"])
        ),
        "phraseology_topic_pages": sum(
            1 for text in texts if any(marker in text.lower() for marker in intake.CONTENT_FIT_MARKERS["phraseology"])
        ),
        "lexicology_topic_pages": sum(
            1 for text in texts if any(marker in text.lower() for marker in intake.CONTENT_FIT_MARKERS["lexicology"])
        ),
        "lexicography_topic_pages": sum(
            1 for text in texts if any(marker in text.lower() for marker in intake.CONTENT_FIT_MARKERS["lexicography"])
        ),
        "definition_pages": sum(
            1 for text in texts if any(marker in text.lower() for marker in intake.CONTENT_FIT_MARKERS["definitions"])
        ),
        "theory_classification_pages": sum(
            1
            for text in texts
            if any(marker in text.lower() for marker in intake.CONTENT_FIT_MARKERS["theory_classification"])
        ),
        "example_pages": sum(
            1 for text in texts if any(marker in text.lower() for marker in intake.CONTENT_FIT_MARKERS["examples"])
        ),
        "exercise_pages": sum(
            1 for text in texts if any(marker in text.lower() for marker in intake.CONTENT_FIT_MARKERS["exercises"])
        ),
        "self_control_answer_pages": sum(
            1
            for text in texts
            if any(marker in text.lower() for marker in intake.CONTENT_FIT_MARKERS["self_control_answers"])
        ),
    }
    document_wide_depth = intake._depth_evidence_from_pages(texts)
    topic_conditioned = {
        cell: intake._topic_conditioned_depth(texts, cell)
        for cell in [*intake.PROVISIONAL_NARROW_CELLS, *intake.SECONDARY_OBSERVATION_CELLS]
    }
    intro = texts[: intake.INTRO_PAGE_WINDOW]
    historical_markers = ("давньорус", "походження", "історичн")
    rights = {
        "author_copyright_marker_hits": joined.count("© Ольга Павлушенко"),
        "creative_commons_marker_hits": 0,
        "item_metadata_rights_fields_present": False,
        "landing_creativecommons_org_uri_hits": 0,
        "license_word_hits": joined_lower.count("ліцензі"),
        "university_name_marker_hits": normalized.count("Вінницький державний педагогічний університет"),
    }
    flags = {
        "davnoruska_marker_hits": joined_lower.count("давньорус"),
        "historical_origin_marker_hits": joined_lower.count("давньорус"),
        "historical_origin_pages_in_intro_window": sum(
            1 for page in intro if any(marker in page.lower() for marker in historical_markers)
        ),
        "shared_east_slavic_calque_hits": joined_lower.count("спільносхіднослов") + joined_lower.count("общерус"),
        "russian_comparison_hits": joined_lower.count("російськ") + joined_lower.count("русск"),
        "soviet_era_marker_hits": joined_lower.count("радянськ") + joined_lower.count("ссср"),
        "etymology_marker_hits": joined_lower.count("етимолог"),
        "yazyk_token_hits": joined_lower.count("язик"),
        "adjudication": "pending_independent_ukrainian_canon_review",
        "historical_origin_excluded_from_semantic_gold": True,
        "historical_origin_excluded_from_normative_authority": True,
    }
    return {
        "marker_hits": hits,
        "page_counts": page_counts,
        "document_wide_depth": document_wide_depth,
        "topic_conditioned": topic_conditioned,
        "rights_marker_hits": rights,
        "ukrainian_review_flags": flags,
    }


def _fixture(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> dict[str, Path]:
    private = tmp_path / "private"
    pdf_path = private / "source.pdf"
    landing_path = private / "landing.html"
    item_path = private / "item.json"
    bitstream_path = private / "bitstream.json"
    schema_path = tmp_path / "schema.json"
    pdf_payload = b"fixture vspu pdf bytes"
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
        "pages": len(texts),
        "text_bearing_pages": len(texts),
        "unicode_code_points": sum(len(text) for text in texts),
        "utf8_bytes": sum(len(text.encode("utf-8")) for text in texts),
        "page_manifest_sha256": hashlib.sha256(b"".join(intake.canonical_bytes(row) for row in page_rows)).hexdigest(),
        "extracted_text_sha256": hashlib.sha256("\n\f\n".join(texts).encode("utf-8")).hexdigest(),
    }
    content_fit = _content_fit_from_texts(texts)
    landing_payload = _landing_html().encode("utf-8")
    item_doc = _item_metadata()
    bitstream_doc = _bitstream_metadata()
    bitstream_doc["sizeBytes"] = len(pdf_payload)
    bitstream_doc["checkSum"]["value"] = hashlib.md5(pdf_payload, usedforsecurity=False).hexdigest()
    item_payload = intake.canonical_bytes(item_doc)
    bitstream_payload = intake.canonical_bytes(bitstream_doc)
    _write_private(pdf_path, pdf_payload)
    _write_private(landing_path, landing_payload)
    _write_private(item_path, item_payload)
    _write_private(bitstream_path, bitstream_payload)

    monkeypatch.setattr(intake, "PDF_SHA256", hashlib.sha256(pdf_payload).hexdigest())
    monkeypatch.setattr(intake, "PDF_MD5", hashlib.md5(pdf_payload, usedforsecurity=False).hexdigest())
    monkeypatch.setattr(intake, "PDF_BYTES", len(pdf_payload))
    monkeypatch.setattr(intake, "PDF_PAGE_OBJECTS", len(texts))
    monkeypatch.setattr(intake, "CATALOG_CITATION_PAGES", len(texts) + 1)
    monkeypatch.setattr(intake, "TEXT_BEARING_PAGES", len(texts))
    monkeypatch.setattr(intake, "UNICODE_CODE_POINTS", text_facts["unicode_code_points"])
    monkeypatch.setattr(intake, "UTF8_BYTES", text_facts["utf8_bytes"])
    monkeypatch.setattr(intake, "PAGE_MANIFEST_SHA256", text_facts["page_manifest_sha256"])
    monkeypatch.setattr(intake, "EXTRACTED_TEXT_SHA256", text_facts["extracted_text_sha256"])
    monkeypatch.setattr(intake, "LANDING_SHA256", hashlib.sha256(landing_payload).hexdigest())
    monkeypatch.setattr(intake, "LANDING_BYTES", len(landing_payload))
    monkeypatch.setattr(intake, "ITEM_METADATA_SHA256", hashlib.sha256(item_payload).hexdigest())
    monkeypatch.setattr(intake, "ITEM_METADATA_BYTES", len(item_payload))
    monkeypatch.setattr(intake, "BITSTREAM_METADATA_SHA256", hashlib.sha256(bitstream_payload).hexdigest())
    monkeypatch.setattr(intake, "BITSTREAM_METADATA_BYTES", len(bitstream_payload))
    monkeypatch.setattr(intake, "PRIVATE_JSONL_BYTES", 1)
    monkeypatch.setattr(intake, "PRIVATE_JSONL_SHA256", "a" * 64)
    monkeypatch.setattr(intake, "EXACTNESS_AUDIT_SHA256", "b" * 64)
    monkeypatch.setattr(intake, "CONTENT_FIT_MARKER_HITS", content_fit["marker_hits"])
    monkeypatch.setattr(intake, "CONTENT_FIT_PAGE_COUNTS", content_fit["page_counts"])
    monkeypatch.setattr(intake, "CONTENT_FIT_DOCUMENT_WIDE_DEPTH", content_fit["document_wide_depth"])
    monkeypatch.setattr(intake, "CONTENT_FIT_TOPIC_CONDITIONED", content_fit["topic_conditioned"])
    monkeypatch.setattr(intake, "RIGHTS_MARKER_HITS", content_fit["rights_marker_hits"])
    monkeypatch.setattr(intake, "UKRAINIAN_REVIEW_FLAGS", content_fit["ukrainian_review_flags"])
    monkeypatch.setattr(intake, "PdfReader", lambda path: _FakeReader(path, texts))
    monkeypatch.setattr(
        intake,
        "detect_native_text_anomalies",
        lambda text: {"requires_visual_verification": False},
    )
    schema_path.write_text('{"type":"object"}\n', encoding="utf-8")
    monkeypatch.setattr(intake, "SCHEMA_PATH", schema_path)

    records = [intake._page_record(index, text) for index, text in enumerate(texts, start=1)]
    jsonl_path = private / "processed" / "grade-00" / intake.JSONL_FILENAME
    payload = b"".join(intake.canonical_bytes(record) for record in records)
    _write_private(jsonl_path, payload)
    monkeypatch.setattr(intake, "PRIVATE_JSONL_BYTES", len(payload))
    monkeypatch.setattr(intake, "PRIVATE_JSONL_SHA256", hashlib.sha256(payload).hexdigest())

    exactness = {
        "schema_version": "textbook-native-exactness-audit.v1",
        "source_count": 1,
        "chunk_total": len(texts),
        "flagged_source_count": 0,
        "flagged_chunk_count": 0,
        "verified_flagged_chunk_count": 0,
        "unverified_flagged_chunk_count": 0,
        "flagged_page_count": 0,
        "clean_chunk_count": len(texts),
        "source_file": intake.SOURCE_ID,
        "relative_jsonl": f"grade-00/{intake.JSONL_FILENAME}",
        "jsonl_sha256": hashlib.sha256(payload).hexdigest(),
    }
    exactness_path = private / "exactness" / intake.EXACTNESS_AUDIT_FILENAME
    exactness_payload = intake.canonical_bytes(exactness)
    _write_private(exactness_path, exactness_payload)
    monkeypatch.setattr(intake, "EXACTNESS_AUDIT_SHA256", hashlib.sha256(exactness_payload).hexdigest())

    custody = {
        "google_drive_custody": True,
        "google_drive_mount_containment_verified": True,
        "google_drive_provider_identity_present": True,
        "google_drive_provider_identity_sha256": {
            "bitstream_metadata": "a" * 64,
            "content_fit_audit": "b" * 64,
            "exactness_audit": "c" * 64,
            "item_metadata": "d" * 64,
            "landing_html": "e" * 64,
            "private_jsonl": "f" * 64,
            "source_pdf": "1" * 64,
        },
        "drive_relative_directory": intake.PRIVATE_INPUT_LOCATOR,
        "private_files_mode_0600": True,
        "private_directory_mode_0700": True,
        "all_new_files_readback_hash_match": True,
        "artifacts": {
            "source_pdf": intake.PDF_FILENAME,
            "landing_html": intake.LANDING_FILENAME,
            "item_metadata": intake.ITEM_METADATA_FILENAME,
            "bitstream_metadata": intake.BITSTREAM_METADATA_FILENAME,
            "private_jsonl": f"processed/grade-00/{intake.JSONL_FILENAME}",
            "exactness_audit": f"exactness/{intake.EXACTNESS_AUDIT_FILENAME}",
            "content_fit_audit": intake.CONTENT_FIT_AUDIT_FILENAME,
            "custody_receipt": intake.CUSTODY_RECEIPT_FILENAME,
            "checksums": intake.CHECKSUMS_FILENAME,
        },
    }
    custody_doc = {
        "schema_version": "phase3_vspu_2025_morphemics_word_formation_custody_receipt_v1",
        "text_free": True,
        "provider_calls": False,
        "semantic_gold": False,
        "custody": custody,
    }
    custody_doc["receipt_sha256"] = intake.receipt_sha256(custody_doc)
    custody_path = private / intake.CUSTODY_RECEIPT_FILENAME
    _write_private(custody_path, intake.canonical_bytes(custody_doc))

    return {
        "pdf": pdf_path,
        "landing": landing_path,
        "item": item_path,
        "bitstream": bitstream_path,
        "jsonl": jsonl_path,
        "exactness": exactness_path,
        "custody": custody_path,
        "schema": schema_path,
    }


def _build(paths: dict[str, Path]) -> dict[str, object]:
    return intake.build_receipt(
        source_pdf=paths["pdf"],
        landing_html=paths["landing"],
        item_metadata=paths["item"],
        bitstream_metadata=paths["bitstream"],
        private_jsonl=paths["jsonl"],
        exactness_audit=paths["exactness"],
        custody_receipt=paths["custody"],
    )


def test_contract_schema_is_valid_and_text_free() -> None:
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    schema_text = SCHEMA.read_text(encoding="utf-8")
    assert '"source_text"' not in schema_text
    assert '"page_texts"' not in schema_text
    assert "GoogleDrive-" not in schema_text


def test_build_is_deterministic_and_preserves_false_completion_gates(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    paths = _fixture(tmp_path, monkeypatch)
    first = _build(paths)
    second = _build(paths)
    assert first == second
    assert first["status"] == intake.STATUS
    assert first["review_scope"]["topic_gaps_closed"] == []  # type: ignore[index]
    assert first["review_scope"]["topic_gaps_narrowed"] == []  # type: ignore[index]
    assert first["content_fitness"]["topic_gaps_narrowed_claimed"] == []  # type: ignore[index]
    assert first["rights"]["rights_statement"] == intake.RIGHTS_STATEMENT  # type: ignore[index]
    assert first["rights"]["public_redistribution_authorized"] is False  # type: ignore[index]
    assert first["rights"]["unrestricted_training_export_authorized"] is False  # type: ignore[index]
    assert first["gates"]["semantic_gold"] is False  # type: ignore[index]
    assert first["gates"]["phase3_complete"] is False  # type: ignore[index]
    assert first["gates"]["phase4_blocked"] is True  # type: ignore[index]
    assert first["denominators"]["v2_source_units"] == 67041  # type: ignore[index]
    assert first["denominators"]["v2_evaluation_identities"] == 9392  # type: ignore[index]
    assert first["denominators"]["phase3_labels"] == 0  # type: ignore[index]
    assert first["denominators"]["candidate_source_count"] == 30  # type: ignore[index]
    assert first["denominators"]["database_resident_source_count"] == 20  # type: ignore[index]
    assert first["denominators"]["reference_only_source_count"] == 6  # type: ignore[index]
    assert first["denominators"]["quarantine_source_count"] == 4  # type: ignore[index]
    assert first["text_layer"]["page_count_discrepancy"]["recorded_without_correction"] is True  # type: ignore[index]
    assert first["content_fitness"]["secondary_observation_cells"]["semantics"]["role"] == "secondary_observation"


def test_pdf_byte_drift_is_rejected(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    paths = _fixture(tmp_path, monkeypatch)
    paths["pdf"].write_bytes(b"changed")
    os.chmod(paths["pdf"], 0o600)
    with pytest.raises(
        intake.Vspu2025MorphemicsWordFormationIntakeError, match=r"byte denominator drift|SHA-256 drift"
    ):
        _build(paths)


def test_landing_license_uri_is_rejected(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    paths = _fixture(tmp_path, monkeypatch)
    html = paths["landing"].read_text(encoding="utf-8") + '<a href="https://creativecommons.org/licenses/by/4.0/">'
    _write_private(paths["landing"], html.encode("utf-8"))
    monkeypatch.setattr(intake, "LANDING_SHA256", intake.sha256_file(paths["landing"]))
    monkeypatch.setattr(intake, "LANDING_BYTES", paths["landing"].stat().st_size)
    with pytest.raises(intake.Vspu2025MorphemicsWordFormationIntakeError, match="Creative Commons URI"):
        _build(paths)


def test_missing_page_text_is_rejected(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    paths = _fixture(tmp_path, monkeypatch)
    texts = _page_texts()
    texts[1] = ""
    monkeypatch.setattr(intake, "PdfReader", lambda path: _FakeReader(path, texts))
    with pytest.raises(intake.Vspu2025MorphemicsWordFormationIntakeError, match="has no embedded text"):
        _build(paths)


def test_native_anomaly_is_rejected(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    paths = _fixture(tmp_path, monkeypatch)
    monkeypatch.setattr(
        intake,
        "detect_native_text_anomalies",
        lambda text: {"requires_visual_verification": True},
    )
    with pytest.raises(intake.Vspu2025MorphemicsWordFormationIntakeError, match="native exactness defects"):
        _build(paths)


def test_private_mode_and_symlink_are_rejected(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    paths = _fixture(tmp_path, monkeypatch)
    _simulate_group_readable_mode(monkeypatch, paths["pdf"])
    with pytest.raises(intake.Vspu2025MorphemicsWordFormationIntakeError, match="mode 0600"):
        _build(paths)
    link = tmp_path / "source-link.pdf"
    link.symlink_to(paths["pdf"])
    paths["pdf"] = link
    with pytest.raises(intake.Vspu2025MorphemicsWordFormationIntakeError, match=r"regular file|symbolic-link"):
        _build(paths)


def test_stale_jsonl_binding_is_rejected(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    paths = _fixture(tmp_path, monkeypatch)
    _write_private(paths["jsonl"], b'{"tampered":true}\n')
    with pytest.raises(intake.Vspu2025MorphemicsWordFormationIntakeError, match="private JSONL replay drift"):
        _build(paths)


def test_public_receipt_is_immutable(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    paths = _fixture(tmp_path, monkeypatch)
    receipt = _build(paths)
    out = tmp_path / "git" / "receipt.json"
    out.parent.mkdir(parents=True)
    (out.parent / ".git").mkdir()
    intake.write_public_receipt(out, receipt)
    assert stat.S_IMODE(out.stat().st_mode) == intake.PRIVATE_FILE_MODE
    intake.write_public_receipt(out, receipt)
    other = dict(receipt)
    other["status"] = "TAMPERED"
    other["receipt_sha256"] = intake.receipt_sha256(other)
    with pytest.raises(intake.Vspu2025MorphemicsWordFormationIntakeError, match="immutable public receipt"):
        intake.write_public_receipt(out, other)


def test_public_receipt_accepts_existing_tracked_checkout_mode(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    paths = _fixture(tmp_path, monkeypatch)
    receipt = _build(paths)
    out = tmp_path / "git" / "receipt.json"
    out.parent.mkdir(parents=True)
    (out.parent / ".git").mkdir()
    payload = intake.canonical_bytes(receipt)
    out.write_bytes(payload)
    os.chmod(out, intake.PRIVATE_FILE_MODE)

    real_lstat = Path.lstat

    def lstat_with_tracked_checkout_mode(path: Path) -> os.stat_result:
        result = real_lstat(path)
        if path == out:
            mode = (result.st_mode & ~0o777) | intake.TRACKED_PUBLIC_FILE_MODE
            return os.stat_result((mode, *result[1:]))
        return result

    monkeypatch.setattr(Path, "lstat", lstat_with_tracked_checkout_mode)
    assert stat.S_IMODE(os.lstat(out).st_mode) == intake.PRIVATE_FILE_MODE
    assert stat.S_IMODE(out.lstat().st_mode) == intake.TRACKED_PUBLIC_FILE_MODE
    intake.write_public_receipt(out, receipt)
    assert out.read_bytes() == payload
    assert stat.S_IMODE(os.lstat(out).st_mode) == intake.PRIVATE_FILE_MODE
    other = dict(receipt)
    other["status"] = "TAMPERED"
    other["receipt_sha256"] = intake.receipt_sha256(other)
    with pytest.raises(intake.Vspu2025MorphemicsWordFormationIntakeError, match="immutable public receipt"):
        intake.write_public_receipt(out, other)


def test_concurrent_receipt_creation_cannot_clobber_winner(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    paths = _fixture(tmp_path, monkeypatch)
    receipt = _build(paths)
    out = tmp_path / "git" / "receipt.json"
    out.parent.mkdir(parents=True)
    (out.parent / ".git").mkdir()

    def concurrent_link(source: Path, destination: Path, *, follow_symlinks: bool = True) -> None:
        out.write_bytes(b'{"winner":true}\n')
        os.chmod(out, 0o600)
        raise FileExistsError

    monkeypatch.setattr(os, "link", concurrent_link)
    with pytest.raises(intake.Vspu2025MorphemicsWordFormationIntakeError, match="immutable public receipt"):
        intake.write_public_receipt(out, receipt)
    assert out.read_bytes() == b'{"winner":true}\n'


def test_atomic_write_api_has_no_mode_parameter() -> None:
    import inspect

    params = inspect.signature(intake._atomic_write).parameters
    assert list(params) == ["path", "payload"]
    assert "mode" not in params
    assert intake.PRIVATE_FILE_MODE == 0o600
    assert intake.TRACKED_PUBLIC_FILE_MODE == 0o644
    assert frozenset({0o600, 0o644}) == intake.ACCEPTED_PUBLIC_RECEIPT_MODES


def test_topic_conditioned_depth_ignores_off_topic_marker_pages() -> None:
    morphemics_page = "морфеміка визначення класифікація наприклад завдання"
    word_formation_page = "словотвір визначення класифікація наприклад завдання"
    off_topic_depth_page = "визначення класифікація наприклад завдання самоконтроль відповіді " * 20
    pages = [morphemics_page, word_formation_page, off_topic_depth_page]
    conditioned = {cell: intake._topic_conditioned_depth(pages, cell) for cell in ("morphemics", "word_formation")}
    document_wide = intake._depth_evidence_from_pages(pages)
    assert conditioned["morphemics"]["definition_marker_hits"] == 1
    assert conditioned["word_formation"]["definition_marker_hits"] == 1
    assert document_wide["definition_marker_hits"] == 22
    assert conditioned["morphemics"]["definition_marker_hits"] < document_wide["definition_marker_hits"]
    assert conditioned["word_formation"]["definition_marker_hits"] < document_wide["definition_marker_hits"]
    assert conditioned["morphemics"]["exercise_pages"] == 1
    assert conditioned["word_formation"]["exercise_pages"] == 1
    assert document_wide["exercise_pages"] == 3


def test_validate_receipt_rebinds_university_freeze_and_policy(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    paths = _fixture(tmp_path, monkeypatch)
    receipt = _build(paths)
    intake.validate_receipt(receipt)

    tampered_freeze = tmp_path / "freeze.json"
    tampered_freeze.write_bytes(b'{"tampered":true}\n')
    monkeypatch.setattr(intake, "UNIVERSITY_FREEZE_PATH", tampered_freeze)
    with pytest.raises(intake.Vspu2025MorphemicsWordFormationIntakeError, match="university content-audit freeze"):
        intake.validate_receipt(receipt)

    monkeypatch.setattr(
        intake, "UNIVERSITY_FREEZE_PATH", intake.DATA / "admission/phase3_university_content_audit_freeze_v1.json"
    )
    tampered_policy = tmp_path / "policy.json"
    tampered_policy.write_bytes(b'{"tampered":true}\n')
    monkeypatch.setattr(intake, "SOURCE_POLICY_PATH", tampered_policy)
    with pytest.raises(intake.Vspu2025MorphemicsWordFormationIntakeError, match="complete source policy v4"):
        intake.validate_receipt(receipt)


def test_validate_receipt_rejects_overclaims(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    paths = _fixture(tmp_path, monkeypatch)
    receipt = _build(paths)
    receipt["review_scope"]["topic_gaps_closed"] = ["morphemics"]  # type: ignore[index]
    receipt["receipt_sha256"] = intake.receipt_sha256(receipt)
    with pytest.raises(intake.Vspu2025MorphemicsWordFormationIntakeError, match=r"closed topic gap|schema violation"):
        intake.validate_receipt(receipt)


@pytest.mark.parametrize(
    ("field", "forged_value", "match"),
    [
        ("private_jsonl_sha256", "0" * 64, r"private JSONL hash drift|schema violation"),
        ("private_jsonl_bytes", 1, r"private JSONL byte denominator drift|schema violation"),
        ("exactness_audit_sha256", "0" * 64, r"exactness audit hash drift|schema violation"),
    ],
)
def test_validate_receipt_rejects_resealed_private_custody_binding_mutations(
    field: str, forged_value: object, match: str
) -> None:
    if not PUBLIC_RECEIPT.is_file():
        pytest.skip("public receipt not materialized yet")
    receipt = json.loads(PUBLIC_RECEIPT.read_text(encoding="utf-8"))
    forged = copy.deepcopy(receipt)
    forged["bindings"][field] = forged_value
    forged["receipt_sha256"] = intake.receipt_sha256(forged)
    with pytest.raises(intake.Vspu2025MorphemicsWordFormationIntakeError, match=match):
        intake.validate_receipt(forged)


def test_committed_receipt_validates_when_present() -> None:
    if not PUBLIC_RECEIPT.is_file():
        pytest.skip("public receipt not materialized yet")
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    receipt = json.loads(PUBLIC_RECEIPT.read_text(encoding="utf-8"))
    Draft202012Validator(schema).validate(receipt)
    validated = intake.validate_receipt(receipt)
    assert validated["receipt_sha256"] == intake.receipt_sha256(validated)
    assert validated["status"] == intake.STATUS
    assert validated["bindings"]["source_pdf_sha256"] == intake.PDF_SHA256
    assert validated["bindings"]["source_pdf_bytes"] == intake.PDF_BYTES
    assert validated["bindings"]["private_jsonl_sha256"] == intake.PRIVATE_JSONL_SHA256
    assert validated["bindings"]["private_jsonl_bytes"] == intake.PRIVATE_JSONL_BYTES
    assert validated["bindings"]["exactness_audit_sha256"] == intake.EXACTNESS_AUDIT_SHA256
    assert validated["bindings"]["content_fit_audit_sha256"] == intake.CONTENT_FIT_AUDIT_SHA256
    assert validated["bindings"]["university_content_audit_freeze_v1_sha256"] == intake.UNIVERSITY_FREEZE_SHA256
    assert validated["bindings"]["complete_source_policy_v4_sha256"] == intake.SOURCE_POLICY_SHA256
    assert validated["bindings"]["custody_receipt_file_sha256"] == intake.CUSTODY_RECEIPT_FILE_SHA256
    assert validated["bindings"]["custody_receipt_body_sha256"] == intake.CUSTODY_RECEIPT_BODY_SHA256
    assert validated["native_exactness"]["flagged_chunk_count"] == 0
    assert validated["review_scope"]["topic_gaps_narrowed"] == []
    assert validated["content_fitness"]["cells"]["morphemics"]["depth_evidence"]["scope"] == "topic_conditioned"
    assert validated["content_fitness"]["cells"]["word_formation"]["depth_evidence"]["scope"] == "topic_conditioned"
    assert validated["content_fitness"]["document_wide_depth_evidence"]["scope"] == "document_wide"
    assert validated["rights"]["rights_statement"] == intake.RIGHTS_STATEMENT
    assert validated["gates"]["phase3_complete"] is False
    assert validated["gates"]["phase4_blocked"] is True
    dumped = json.dumps(validated, ensure_ascii=False)
    assert "GoogleDrive-" not in dumped
    assert "@gmail.com" not in dumped
    assert "\f" not in dumped


def test_production_verify_against_drive_custody() -> None:
    if not PUBLIC_RECEIPT.is_file():
        pytest.skip("public receipt not materialized yet")
    drive_staging = _drive_staging()
    if drive_staging is None:
        pytest.skip("configured Drive mount unavailable")
    pdf = drive_staging / intake.PDF_FILENAME
    landing = drive_staging / intake.LANDING_FILENAME
    item = drive_staging / intake.ITEM_METADATA_FILENAME
    bitstream = drive_staging / intake.BITSTREAM_METADATA_FILENAME
    jsonl = drive_staging / "processed" / "grade-00" / intake.JSONL_FILENAME
    exactness = drive_staging / "exactness" / intake.EXACTNESS_AUDIT_FILENAME
    custody = drive_staging / intake.CUSTODY_RECEIPT_FILENAME
    checksums = drive_staging / intake.CHECKSUMS_FILENAME
    content_fit = drive_staging / intake.CONTENT_FIT_AUDIT_FILENAME
    required = [drive_staging, pdf, landing, item, bitstream, jsonl, exactness, custody, checksums, content_fit]
    if not all(path.exists() for path in required):
        pytest.skip("Drive custody artifacts unavailable")
    assert stat.S_IMODE(drive_staging.stat().st_mode) == 0o700
    for path in (pdf, landing, item, bitstream, jsonl, exactness, custody, checksums, content_fit):
        assert stat.S_IMODE(path.stat().st_mode) == 0o600
    assert intake.sha256_file(pdf) == intake.PDF_SHA256
    assert pdf.stat().st_size == intake.PDF_BYTES
    assert intake.sha256_file(landing) == intake.LANDING_SHA256
    assert intake.sha256_file(custody) == intake.CUSTODY_RECEIPT_FILE_SHA256
    assert intake.sha256_file(checksums) == intake.CHECKSUMS_SHA256
    committed = json.loads(PUBLIC_RECEIPT.read_text(encoding="utf-8"))
    assert committed["bindings"]["private_jsonl_sha256"] == intake.sha256_file(jsonl)
    assert committed["bindings"]["exactness_audit_sha256"] == intake.sha256_file(exactness)
    assert committed["custody"]["all_new_files_readback_hash_match"] is True
    reproduced = intake.production_run(
        staging_root=drive_staging,
        public_receipt_path=PUBLIC_RECEIPT,
    )
    assert reproduced["receipt_sha256"] == committed["receipt_sha256"]
    assert reproduced["native_exactness"]["flagged_chunk_count"] == 0
    assert reproduced["gates"]["phase4_blocked"] is True
    assert reproduced["content_fitness"]["cells"]["morphemics"]["depth_evidence"]["topic_marker_hits"] == 346
    assert reproduced["content_fitness"]["cells"]["word_formation"]["depth_evidence"]["topic_marker_hits"] == 210
    assert reproduced["content_fitness"]["document_wide_depth_evidence"]["definition_marker_hits"] == 17
