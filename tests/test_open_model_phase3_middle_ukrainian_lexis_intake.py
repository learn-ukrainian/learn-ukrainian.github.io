from __future__ import annotations

import hashlib
import json
import os
import struct
import zlib
from pathlib import Path

import pytest

from scripts.projects.open_model_data import phase3_middle_ukrainian_lexis_intake as intake
from scripts.projects.open_model_data.phase3_linguistic_representation import sha256_value
from scripts.projects.open_model_data.phase3_middle_ukrainian_lexis_intake import (
    MiddleUkrainianLexisIntakeError,
)


def _png_chunk(chunk_type: bytes, payload: bytes) -> bytes:
    crc = zlib.crc32(chunk_type)
    crc = zlib.crc32(payload, crc) & 0xFFFFFFFF
    return struct.pack(">I", len(payload)) + chunk_type + payload + struct.pack(">I", crc)


def _fixture_png() -> bytes:
    ihdr = struct.pack(">IIBBBBB", 1, 1, 1, 0, 0, 0, 0)
    scanline = zlib.compress(b"\x00\x00")
    return intake.PNG_SIGNATURE + _png_chunk(b"IHDR", ihdr) + _png_chunk(b"IDAT", scanline) + _png_chunk(b"IEND", b"")


def _html(body: str) -> bytes:
    return (
        '<html><head><meta http-equiv="Content-Type" content="text/html; charset=windows-1251"></head>'
        f"<body>{body}</body></html>"
    ).encode("windows-1251")


def _write_private_file(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    os.chmod(path.parent, 0o700)
    path.write_bytes(data)
    os.chmod(path, 0o600)


def _fixture_snapshot(root: Path) -> None:
    root.mkdir()
    os.chmod(root, 0o700)
    _write_private_file(
        root / "zyzlex/zyz.htm",
        _html(
            '<a href="zyz01.htm">editorial</a><a href="zyz02.htm">scan</a>'
            '<link href="zyz.css"><link href="../zsuv.css">'
        ),
    )
    _write_private_file(root / "zyzlex/zyz01.htm", _html('<a href="zyz.htm">home</a>'))
    _write_private_file(
        root / "zyzlex/zyz02.htm",
        _html('<a href="zyz.htm">home</a><img src="zyzle001.png">'),
    )
    _write_private_file(root / "zyzlex/zyzle001.png", _fixture_png())
    _write_private_file(root / "zyzlex/zyz.css", b"body { color: black; }\n")
    _write_private_file(root / "zsuv.css", b"html { background: white; }\n")


def _patch_fixture_contract(
    monkeypatch: pytest.MonkeyPatch,
    snapshot_dir: Path,
    schema_path: Path,
) -> None:
    html_paths = ("zyzlex/zyz.htm", "zyzlex/zyz01.htm", "zyzlex/zyz02.htm")
    png_paths = ("zyzlex/zyzle001.png",)
    css_paths = ("zsuv.css", "zyzlex/zyz.css")
    expected_paths = tuple(sorted((*html_paths, *png_paths, *css_paths)))
    monkeypatch.setattr(intake, "HTML_PATHS", html_paths)
    monkeypatch.setattr(intake, "PNG_PATHS", png_paths)
    monkeypatch.setattr(intake, "CSS_PATHS", css_paths)
    monkeypatch.setattr(intake, "EXPECTED_RESOURCE_PATHS", expected_paths)
    monkeypatch.setattr(intake, "INDEX_HTML_PATHS", ("zyzlex/zyz.htm",))
    monkeypatch.setattr(intake, "EDITORIAL_HTML_PATHS", ("zyzlex/zyz01.htm",))
    monkeypatch.setattr(intake, "TARGET_TRANSCRIPTION_HTML_PATHS", ())
    monkeypatch.setattr(intake, "SUPPLEMENTAL_TRANSCRIPTION_HTML_PATHS", ())
    monkeypatch.setattr(intake, "FACSIMILE_WRAPPER_HTML_PATHS", ("zyzlex/zyz02.htm",))
    monkeypatch.setattr(
        intake,
        "FACSIMILE_PAGE_IMAGE_PAIRS",
        (("zyzlex/zyz02.htm", "zyzlex/zyzle001.png"),),
    )

    manifest: list[dict[str, object]] = []
    png_structures: list[dict[str, object]] = []
    category_bytes = {"html": 0, "png": 0, "css": 0}
    for relative_path in expected_paths:
        data = (snapshot_dir / relative_path).read_bytes()
        manifest.append(
            {
                "path": relative_path,
                "bytes": len(data),
                "sha256": hashlib.sha256(data).hexdigest(),
            }
        )
        if relative_path.endswith(".htm"):
            category_bytes["html"] += len(data)
        elif relative_path.endswith(".png"):
            category_bytes["png"] += len(data)
            png_structures.append(intake._inspect_png(data, path=relative_path))
        else:
            category_bytes["css"] += len(data)

    monkeypatch.setattr(intake, "EXPECTED_RESOURCE_COUNT", len(expected_paths))
    monkeypatch.setattr(intake, "EXPECTED_HTML_COUNT", len(html_paths))
    monkeypatch.setattr(intake, "EXPECTED_PNG_COUNT", len(png_paths))
    monkeypatch.setattr(intake, "EXPECTED_CSS_COUNT", len(css_paths))
    monkeypatch.setattr(intake, "EXPECTED_TOTAL_BYTES", sum(item["bytes"] for item in manifest))
    monkeypatch.setattr(intake, "EXPECTED_HTML_BYTES", category_bytes["html"])
    monkeypatch.setattr(intake, "EXPECTED_PNG_BYTES", category_bytes["png"])
    monkeypatch.setattr(intake, "EXPECTED_CSS_BYTES", category_bytes["css"])
    monkeypatch.setattr(intake, "EXPECTED_RESOURCE_MANIFEST_SHA256", sha256_value(manifest))
    monkeypatch.setattr(intake, "EXPECTED_PNG_STRUCTURE_MANIFEST_SHA256", sha256_value(png_structures))
    monkeypatch.setattr(intake, "EXPECTED_REFERENCE_MANIFEST_SHA256", sha256_value(sorted(expected_paths)))
    monkeypatch.setattr(intake, "RECEIPT_SCHEMA_PATH", schema_path)


def test_png_walker_validates_exact_structure_and_crc() -> None:
    structure = intake._inspect_png(_fixture_png(), path="fixture.png")

    assert structure == {
        "path": "fixture.png",
        "width": 1,
        "height": 1,
        "bit_depth": 1,
        "color_type": 0,
        "interlace": 0,
    }


def test_png_walker_rejects_crc_drift_and_trailing_bytes() -> None:
    bad_crc = bytearray(_fixture_png())
    bad_crc[-1] ^= 1
    with pytest.raises(MiddleUkrainianLexisIntakeError, match="PNG CRC drift"):
        intake._inspect_png(bytes(bad_crc), path="bad-crc.png")

    with pytest.raises(MiddleUkrainianLexisIntakeError, match="trailing bytes"):
        intake._inspect_png(_fixture_png() + b"x", path="trailing.png")


def test_png_walker_rejects_missing_iend_and_wrong_pixel_format() -> None:
    missing_iend = _fixture_png()[: -len(_png_chunk(b"IEND", b""))]
    with pytest.raises(MiddleUkrainianLexisIntakeError, match="did not close"):
        intake._inspect_png(missing_iend, path="missing-iend.png")

    wrong_ihdr = struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0)
    wrong_format = (
        intake.PNG_SIGNATURE
        + _png_chunk(b"IHDR", wrong_ihdr)
        + _png_chunk(b"IDAT", zlib.compress(b"\x00\x00\x00\x00"))
        + _png_chunk(b"IEND", b"")
    )
    with pytest.raises(MiddleUkrainianLexisIntakeError, match="pixel format drift"):
        intake._inspect_png(wrong_format, path="wrong-format.png")


def test_inspect_snapshot_closes_exact_inventory_links_and_layers(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    snapshot_dir = tmp_path / "snapshot"
    schema_path = tmp_path / "schema.json"
    schema_path.write_text('{"type":"object"}\n', encoding="utf-8")
    os.chmod(schema_path, 0o600)
    _fixture_snapshot(snapshot_dir)
    _patch_fixture_contract(monkeypatch, snapshot_dir, schema_path)

    summary = intake.inspect_snapshot(snapshot_dir)

    assert summary["resources"] == 6
    assert summary["html_pages"] == 3
    assert summary["facsimile_png_assets"] == 1
    assert summary["source_specific_reference_paths"] == 6
    assert summary["facsimile_page_image_links"] == 1
    assert summary["raw_snapshot_fully_walked"] is True


def test_snapshot_rejects_unreferenced_expected_resource_even_when_hashes_match(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    snapshot_dir = tmp_path / "snapshot"
    schema_path = tmp_path / "schema.json"
    schema_path.write_text('{"type":"object"}\n', encoding="utf-8")
    os.chmod(schema_path, 0o600)
    _fixture_snapshot(snapshot_dir)
    root_html = snapshot_dir / "zyzlex/zyz.htm"
    root_html.write_bytes(root_html.read_bytes().replace(b"zyz01.htm", b"zyz99.htm"))
    os.chmod(root_html, 0o600)
    _patch_fixture_contract(monkeypatch, snapshot_dir, schema_path)

    with pytest.raises(MiddleUkrainianLexisIntakeError, match="reference closure drift"):
        intake.inspect_snapshot(snapshot_dir)


def test_snapshot_rejects_html_charset_drift_even_when_hashes_match(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    snapshot_dir = tmp_path / "snapshot"
    schema_path = tmp_path / "schema.json"
    schema_path.write_text('{"type":"object"}\n', encoding="utf-8")
    os.chmod(schema_path, 0o600)
    _fixture_snapshot(snapshot_dir)
    editorial = snapshot_dir / "zyzlex/zyz01.htm"
    editorial.write_bytes(editorial.read_bytes().replace(b"windows-1251", b"x-invalid-xx"))
    os.chmod(editorial, 0o600)
    _patch_fixture_contract(monkeypatch, snapshot_dir, schema_path)

    with pytest.raises(MiddleUkrainianLexisIntakeError, match="charset declaration drift"):
        intake.inspect_snapshot(snapshot_dir)


def test_snapshot_rejects_facsimile_pair_identity_drift(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    snapshot_dir = tmp_path / "snapshot"
    schema_path = tmp_path / "schema.json"
    schema_path.write_text('{"type":"object"}\n', encoding="utf-8")
    os.chmod(schema_path, 0o600)
    _fixture_snapshot(snapshot_dir)
    _patch_fixture_contract(monkeypatch, snapshot_dir, schema_path)
    monkeypatch.setattr(
        intake,
        "FACSIMILE_PAGE_IMAGE_PAIRS",
        (("zyzlex/zyz01.htm", "zyzlex/zyzle001.png"),),
    )

    with pytest.raises(MiddleUkrainianLexisIntakeError, match="wrapper identity drift"):
        intake.inspect_snapshot(snapshot_dir)


def test_snapshot_rejects_extra_resource_and_unsafe_permissions(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    snapshot_dir = tmp_path / "snapshot"
    schema_path = tmp_path / "schema.json"
    schema_path.write_text('{"type":"object"}\n', encoding="utf-8")
    os.chmod(schema_path, 0o600)
    _fixture_snapshot(snapshot_dir)
    _patch_fixture_contract(monkeypatch, snapshot_dir, schema_path)

    _write_private_file(snapshot_dir / "unexpected.txt", b"unexpected")
    with pytest.raises(MiddleUkrainianLexisIntakeError, match="resource inventory drift"):
        intake.inspect_snapshot(snapshot_dir)
    (snapshot_dir / "unexpected.txt").unlink()

    os.chmod(snapshot_dir / "zyzlex/zyz.css", 0o644)
    with pytest.raises(MiddleUkrainianLexisIntakeError, match="permission bits"):
        intake.inspect_snapshot(snapshot_dir)


def test_snapshot_rejects_symlink_ancestor(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    actual_parent = tmp_path / "actual"
    actual_parent.mkdir()
    snapshot_dir = actual_parent / "snapshot"
    schema_path = tmp_path / "schema.json"
    schema_path.write_text('{"type":"object"}\n', encoding="utf-8")
    os.chmod(schema_path, 0o600)
    _fixture_snapshot(snapshot_dir)
    _patch_fixture_contract(monkeypatch, snapshot_dir, schema_path)
    linked_parent = tmp_path / "linked"
    linked_parent.symlink_to(actual_parent, target_is_directory=True)

    with pytest.raises(MiddleUkrainianLexisIntakeError, match="symbolic-link path component"):
        intake.inspect_snapshot(linked_parent / "snapshot")


def test_snapshot_rejects_symlink_file(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    snapshot_dir = tmp_path / "snapshot"
    schema_path = tmp_path / "schema.json"
    schema_path.write_text('{"type":"object"}\n', encoding="utf-8")
    os.chmod(schema_path, 0o600)
    _fixture_snapshot(snapshot_dir)
    _patch_fixture_contract(monkeypatch, snapshot_dir, schema_path)
    target = snapshot_dir / "real.css"
    _write_private_file(target, b"body { color: black; }\n")
    css_path = snapshot_dir / "zyzlex/zyz.css"
    css_path.unlink()
    css_path.symlink_to(target)

    with pytest.raises(MiddleUkrainianLexisIntakeError, match="unsafe file"):
        intake.inspect_snapshot(snapshot_dir)


def test_materialize_and_validate_private_text_free_receipt(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    snapshot_dir = tmp_path / "snapshot"
    schema_path = tmp_path / "schema.json"
    schema_path.write_text('{"type":"object"}\n', encoding="utf-8")
    os.chmod(schema_path, 0o600)
    _fixture_snapshot(snapshot_dir)
    _patch_fixture_contract(monkeypatch, snapshot_dir, schema_path)
    output_dir = tmp_path / "private-receipt"

    receipt = intake.materialize_intake(snapshot_dir=snapshot_dir, private_output_dir=output_dir)
    result = intake.validate_existing_intake(snapshot_dir=snapshot_dir, private_output_dir=output_dir)

    assert receipt["layer_inventory"]["editorial_and_source_layers_semantically_separated"] is False
    assert receipt["evidence_scope"]["nimchuk_as_sole_periodization_authority"] is False
    assert receipt["rights_and_custody"]["retrieval_transport_authenticated"] is False
    assert receipt["safeguards"]["training_eligible"] is False
    assert receipt["safeguards"]["phase4_blocked"] is True
    assert receipt["residuals"]["private_writing_gap_remains_open"] is True
    assert result["resources"] == 6
    assert result["training_eligible"] is False
    assert result["phase3_complete"] is False
    assert result["phase4_blocked"] is True
    assert stat_mode(output_dir) == 0o700
    assert stat_mode(output_dir / intake.RECEIPT_FILENAME) == 0o600


def stat_mode(path: Path) -> int:
    return path.stat().st_mode & 0o777


def test_same_length_source_tamper_fails_manifest_guard(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    snapshot_dir = tmp_path / "snapshot"
    schema_path = tmp_path / "schema.json"
    schema_path.write_text('{"type":"object"}\n', encoding="utf-8")
    os.chmod(schema_path, 0o600)
    _fixture_snapshot(snapshot_dir)
    _patch_fixture_contract(monkeypatch, snapshot_dir, schema_path)
    output_dir = tmp_path / "private-receipt"
    intake.materialize_intake(snapshot_dir=snapshot_dir, private_output_dir=output_dir)

    css_path = snapshot_dir / "zyzlex/zyz.css"
    data = bytearray(css_path.read_bytes())
    data[-2] ^= 1
    css_path.write_bytes(data)
    os.chmod(css_path, 0o600)
    with pytest.raises(MiddleUkrainianLexisIntakeError, match="denominator drift"):
        intake.validate_existing_intake(snapshot_dir=snapshot_dir, private_output_dir=output_dir)


def test_resealed_receipt_overclaim_is_rejected(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    snapshot_dir = tmp_path / "snapshot"
    schema_path = tmp_path / "schema.json"
    schema_path.write_text('{"type":"object"}\n', encoding="utf-8")
    os.chmod(schema_path, 0o600)
    _fixture_snapshot(snapshot_dir)
    _patch_fixture_contract(monkeypatch, snapshot_dir, schema_path)
    output_dir = tmp_path / "private-receipt"
    intake.materialize_intake(snapshot_dir=snapshot_dir, private_output_dir=output_dir)
    receipt_path = output_dir / intake.RECEIPT_FILENAME
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    receipt["safeguards"]["training_eligible"] = True
    body = {key: value for key, value in receipt.items() if key != "receipt_sha256"}
    receipt["receipt_sha256"] = sha256_value(body)
    receipt_path.write_text(json.dumps(receipt), encoding="utf-8")
    os.chmod(receipt_path, 0o600)

    with pytest.raises(MiddleUkrainianLexisIntakeError, match="overclaims training eligibility"):
        intake.validate_existing_intake(snapshot_dir=snapshot_dir, private_output_dir=output_dir)


def test_receipt_self_hash_and_private_mode_drift_are_rejected(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    snapshot_dir = tmp_path / "snapshot"
    schema_path = tmp_path / "schema.json"
    schema_path.write_text('{"type":"object"}\n', encoding="utf-8")
    os.chmod(schema_path, 0o600)
    _fixture_snapshot(snapshot_dir)
    _patch_fixture_contract(monkeypatch, snapshot_dir, schema_path)
    output_dir = tmp_path / "private-receipt"
    intake.materialize_intake(snapshot_dir=snapshot_dir, private_output_dir=output_dir)
    receipt_path = output_dir / intake.RECEIPT_FILENAME
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    receipt["receipt_sha256"] = "0" * 64
    receipt_path.write_text(json.dumps(receipt), encoding="utf-8")
    os.chmod(receipt_path, 0o600)

    with pytest.raises(MiddleUkrainianLexisIntakeError, match="receipt self-hash drift"):
        intake.validate_existing_intake(snapshot_dir=snapshot_dir, private_output_dir=output_dir)

    receipt = intake.materialize_intake(
        snapshot_dir=snapshot_dir,
        private_output_dir=tmp_path / "second-private-receipt",
    )
    assert receipt["safeguards"]["training_eligible"] is False
    second_receipt_path = tmp_path / "second-private-receipt" / intake.RECEIPT_FILENAME
    os.chmod(second_receipt_path, 0o644)
    with pytest.raises(MiddleUkrainianLexisIntakeError, match="permission bits"):
        intake.validate_existing_intake(
            snapshot_dir=snapshot_dir,
            private_output_dir=tmp_path / "second-private-receipt",
        )


def test_private_output_is_immutable_and_cannot_live_in_git(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    snapshot_dir = tmp_path / "snapshot"
    schema_path = tmp_path / "schema.json"
    schema_path.write_text('{"type":"object"}\n', encoding="utf-8")
    os.chmod(schema_path, 0o600)
    _fixture_snapshot(snapshot_dir)
    _patch_fixture_contract(monkeypatch, snapshot_dir, schema_path)
    existing_output = tmp_path / "private-receipt"
    existing_output.mkdir()

    with pytest.raises(MiddleUkrainianLexisIntakeError, match="already exists"):
        intake.materialize_intake(snapshot_dir=snapshot_dir, private_output_dir=existing_output)

    checkout = tmp_path / "checkout"
    checkout.mkdir()
    (checkout / ".git").mkdir()
    with pytest.raises(MiddleUkrainianLexisIntakeError, match="inside Git"):
        intake.materialize_intake(
            snapshot_dir=snapshot_dir,
            private_output_dir=checkout / "private-receipt",
        )


def test_public_receipt_schema_is_text_free_and_fail_closed() -> None:
    schema = json.loads(intake.RECEIPT_SCHEMA_PATH.read_text(encoding="utf-8"))
    serialized = json.dumps(schema, ensure_ascii=False)

    assert '"source_text"' not in serialized
    assert '"transcription_text"' not in serialized
    assert schema["properties"]["safeguards"]["properties"]["training_eligible"] == {"const": False}
    assert schema["properties"]["safeguards"]["properties"]["semantic_gold"] == {"const": False}
    assert schema["properties"]["safeguards"]["properties"]["phase3_complete"] == {"const": False}
    assert schema["properties"]["safeguards"]["properties"]["phase4_blocked"] == {"const": True}
