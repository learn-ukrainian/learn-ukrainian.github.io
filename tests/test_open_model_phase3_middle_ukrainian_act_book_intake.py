from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from scripts.projects.open_model_data import phase3_middle_ukrainian_act_book_intake as intake
from scripts.projects.open_model_data.phase3_middle_ukrainian_act_book_intake import (
    MiddleUkrainianActBookIntakeError,
)


def _chunk(chunk_id: str, payload: bytes) -> bytes:
    raw = chunk_id.encode("ascii") + len(payload).to_bytes(4, "big") + payload
    return raw + (b"\0" if len(payload) & 1 else b"")


def _component(form_type: str, chunks: list[bytes]) -> bytes:
    content = form_type.encode("ascii") + b"".join(chunks)
    raw = b"FORM" + len(content).to_bytes(4, "big") + content
    return raw + (b"\0" if len(content) & 1 else b"")


def _fixture_djvu() -> bytes:
    components = [
        _component("DJVI", [_chunk("Djbz", b"dictionary")]),
        _component("DJVU", [_chunk("INFO", b"page-one!!"), _chunk("TXTz", b"compressed")]),
        _component("DJVU", [_chunk("INFO", b"page-two!!")]),
    ]
    component_count = len(components)
    dirm_payload_size = 1 + 2 + 4 * component_count + 1
    first_component_offset = 4 + 8 + 4 + 8 + dirm_payload_size + (dirm_payload_size & 1)
    offsets: list[int] = []
    cursor = first_component_offset
    for component in components:
        offsets.append(cursor)
        cursor += len(component)
    directory_payload = (
        bytes([129])
        + component_count.to_bytes(2, "big")
        + b"".join(offset.to_bytes(4, "big") for offset in offsets)
        + b"x"
    )
    content = b"DJVM" + _chunk("DIRM", directory_payload) + b"".join(components)
    return b"AT&T" + b"FORM" + len(content).to_bytes(4, "big") + content


def _patch_fixture_contract(monkeypatch: pytest.MonkeyPatch, source_path: Path, schema_path: Path) -> bytes:
    data = _fixture_djvu()
    source_path.write_bytes(data)
    monkeypatch.setattr(intake, "SOURCE_FILENAME", source_path.name)
    monkeypatch.setattr(intake, "SOURCE_BYTES", len(data))
    monkeypatch.setattr(intake, "SOURCE_SHA256", hashlib.sha256(data).hexdigest())
    monkeypatch.setattr(intake, "EXPECTED_DIRECTORY_FLAGS", 129)
    monkeypatch.setattr(intake, "EXPECTED_COMPONENTS", 3)
    monkeypatch.setattr(intake, "EXPECTED_PAGE_COMPONENTS", 2)
    monkeypatch.setattr(intake, "EXPECTED_SHARED_COMPONENTS", 1)
    monkeypatch.setattr(intake, "EXPECTED_PAGES_WITH_EMBEDDED_TEXT", 1)
    monkeypatch.setattr(intake, "EXPECTED_CHUNK_COUNTS", {"Djbz": 1, "INFO": 2, "TXTz": 1})
    monkeypatch.setattr(intake, "RECEIPT_SCHEMA_PATH", schema_path)
    return data


def test_djvu_parser_walks_exact_components_and_text_chunks() -> None:
    structure = intake.parse_djvu_structure(_fixture_djvu())

    assert structure["container_signature"] == "AT&T/FORM:DJVM"
    assert structure["directory_flags"] == 129
    assert structure["component_count"] == 3
    assert structure["page_components"] == 2
    assert structure["shared_components"] == 1
    assert structure["pages_with_embedded_text"] == 1
    assert structure["chunk_counts"] == {"Djbz": 1, "INFO": 2, "TXTz": 1}
    assert structure["container_fully_walked"] is True


def test_djvu_parser_accepts_unpadded_final_odd_form_at_eof() -> None:
    directory_payload = bytes([129]) + (1).to_bytes(2, "big") + (32).to_bytes(4, "big") + b"x"
    directory = _chunk("DIRM", directory_payload)
    info_without_terminal_padding = b"INFO" + (1).to_bytes(4, "big") + b"x"
    page_content = b"DJVU" + info_without_terminal_padding
    final_page = b"FORM" + len(page_content).to_bytes(4, "big") + page_content
    content = b"DJVM" + directory + final_page
    source = b"AT&T" + b"FORM" + len(content).to_bytes(4, "big") + content

    structure = intake.parse_djvu_structure(source)

    assert structure["component_count"] == 1
    assert structure["page_components"] == 1
    assert structure["chunk_counts"] == {"INFO": 1}
    assert len(final_page) & 1 == 1


def test_djvu_parser_rejects_duplicate_directory_offsets() -> None:
    malformed = bytearray(_fixture_djvu())
    malformed[31:35] = malformed[27:31]

    with pytest.raises(MiddleUkrainianActBookIntakeError, match="duplicated or out of order"):
        intake.parse_djvu_structure(bytes(malformed))


def test_djvu_parser_rejects_page_without_exactly_one_info_chunk() -> None:
    shared = _component("DJVI", [_chunk("Djbz", b"dictionary")])
    page = _component("DJVU", [_chunk("TXTz", b"compressed")])
    components = [shared, page]
    dirm_size = 1 + 2 + 4 * len(components) + 1
    first_offset = 4 + 8 + 4 + 8 + dirm_size + (dirm_size & 1)
    offsets = [first_offset, first_offset + len(shared)]
    payload = bytes([129]) + len(components).to_bytes(2, "big") + b"".join(
        offset.to_bytes(4, "big") for offset in offsets
    ) + b"x"
    content = b"DJVM" + _chunk("DIRM", payload) + b"".join(components)
    malformed = b"AT&T" + b"FORM" + len(content).to_bytes(4, "big") + content

    with pytest.raises(MiddleUkrainianActBookIntakeError, match="must contain one INFO"):
        intake.parse_djvu_structure(malformed)


def test_materialize_and_validate_private_text_free_receipt(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source_path = tmp_path / "fixture.djvu"
    schema_path = tmp_path / "schema.json"
    schema_path.write_text('{"type":"object"}\n', encoding="utf-8")
    _patch_fixture_contract(monkeypatch, source_path, schema_path)
    output_dir = tmp_path / "private-receipt"

    receipt = intake.materialize_intake(source_path=source_path, private_output_dir=output_dir)
    result = intake.validate_existing_intake(source_path=source_path, private_output_dir=output_dir)

    assert receipt["container"]["page_components"] == 2
    assert receipt["container"]["pages_with_embedded_text"] == 1
    assert receipt["evidence_scope"]["historical_stage_assignment"] == "pending_qualified_historical_review"
    assert receipt["rights_and_custody"]["training_export_authorized"] is False
    assert receipt["safeguards"]["embedded_text_extracted"] is False
    assert receipt["safeguards"]["training_eligible"] is False
    assert receipt["safeguards"]["phase4_blocked"] is True
    assert receipt["residuals"]["middle_ukrainian_genre_and_region_gap_closed"] is False
    assert result["page_components"] == 2
    assert result["training_eligible"] is False
    assert result["phase3_complete"] is False
    assert result["phase4_blocked"] is True


def test_same_length_source_tamper_fails_sha256_guard(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source_path = tmp_path / "fixture.djvu"
    schema_path = tmp_path / "schema.json"
    schema_path.write_text('{"type":"object"}\n', encoding="utf-8")
    data = _patch_fixture_contract(monkeypatch, source_path, schema_path)
    output_dir = tmp_path / "private-receipt"
    intake.materialize_intake(source_path=source_path, private_output_dir=output_dir)

    corrupted = bytearray(data)
    corrupted[-1] ^= 1
    source_path.write_bytes(corrupted)
    with pytest.raises(MiddleUkrainianActBookIntakeError, match="source SHA-256 drift"):
        intake.validate_existing_intake(source_path=source_path, private_output_dir=output_dir)


def test_resealed_receipt_overclaim_is_rejected(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source_path = tmp_path / "fixture.djvu"
    schema_path = tmp_path / "schema.json"
    schema_path.write_text(
        json.dumps(
            {
                "type": "object",
                "properties": {
                    "safeguards": {
                        "type": "object",
                        "properties": {"training_eligible": {"const": False}},
                    }
                },
            }
        ),
        encoding="utf-8",
    )
    _patch_fixture_contract(monkeypatch, source_path, schema_path)
    output_dir = tmp_path / "private-receipt"
    intake.materialize_intake(source_path=source_path, private_output_dir=output_dir)
    receipt_path = output_dir / intake.RECEIPT_FILENAME
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    receipt["safeguards"]["training_eligible"] = True
    body = {key: value for key, value in receipt.items() if key != "receipt_sha256"}
    receipt["receipt_sha256"] = intake.sha256_value(body)
    receipt_path.write_text(json.dumps(receipt), encoding="utf-8")

    with pytest.raises(MiddleUkrainianActBookIntakeError, match="schema violation"):
        intake.validate_existing_intake(source_path=source_path, private_output_dir=output_dir)


def test_existing_private_output_directory_is_immutable(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source_path = tmp_path / "fixture.djvu"
    schema_path = tmp_path / "schema.json"
    schema_path.write_text('{"type":"object"}\n', encoding="utf-8")
    _patch_fixture_contract(monkeypatch, source_path, schema_path)
    output_dir = tmp_path / "private-receipt"
    output_dir.mkdir()

    with pytest.raises(MiddleUkrainianActBookIntakeError, match="already exists"):
        intake.materialize_intake(source_path=source_path, private_output_dir=output_dir)


def test_private_receipt_inside_git_checkout_is_rejected(tmp_path: Path) -> None:
    checkout = tmp_path / "checkout"
    checkout.mkdir()
    (checkout / ".git").mkdir()

    with pytest.raises(MiddleUkrainianActBookIntakeError, match="cannot be written inside Git"):
        intake.materialize_intake(
            source_path=tmp_path / "missing.djvu",
            private_output_dir=checkout / "private-receipt",
        )


def test_materialization_failure_leaves_no_partial_directory(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source_path = tmp_path / "fixture.djvu"
    schema_path = tmp_path / "schema.json"
    schema_path.write_text('{"type":"object"}\n', encoding="utf-8")
    _patch_fixture_contract(monkeypatch, source_path, schema_path)
    output_dir = tmp_path / "private-receipt"

    def reject(_receipt: object) -> None:
        raise MiddleUkrainianActBookIntakeError("forced receipt failure")

    monkeypatch.setattr(intake, "_validate_receipt", reject)
    with pytest.raises(MiddleUkrainianActBookIntakeError, match="forced receipt failure"):
        intake.materialize_intake(source_path=source_path, private_output_dir=output_dir)
    assert not output_dir.exists()


def test_public_receipt_schema_is_text_free_and_fail_closed() -> None:
    schema = json.loads(intake.RECEIPT_SCHEMA_PATH.read_text(encoding="utf-8"))
    serialized = json.dumps(schema, ensure_ascii=False)

    assert '"source_text"' not in serialized
    assert schema["properties"]["safeguards"]["properties"]["training_eligible"] == {"const": False}
    assert schema["properties"]["safeguards"]["properties"]["phase3_complete"] == {"const": False}
    assert schema["properties"]["safeguards"]["properties"]["phase4_blocked"] == {"const": True}
