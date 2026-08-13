from __future__ import annotations

import hashlib
import json
import os
import stat
from pathlib import Path
from types import SimpleNamespace

import pytest
from jsonschema import Draft202012Validator

from scripts.projects.open_model_data import phase3_vspu_source_materialization as materialization


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


def _scope_review() -> dict[str, object]:
    return {
        "schema_version": materialization.SCOPE_SCHEMA_VERSION,
        "reviewer_seat": "Scope/Circularity Critic",
        "reviewed_input_sha256": {},
        "denominator": {
            "existing_candidate_sources": 30,
            "additive_candidate_sources": 1,
            "proposed_total_candidate_sources": 31,
            "topic_areas": 26,
        },
        "failure_mode_findings": [],
        "topic_gaps_closed": [],
        "topic_gaps_narrowed": materialization.intake.TOPICS_NARROWED,
        "topic_gaps_unchanged": materialization.intake.TOPICS_UNCHANGED,
        "source_disposition": "admit_scoped_candidate",
        "private_page_materialization_authorized": True,
        "database_ingest_prerequisites": [],
        "source_wide_normative_authority": False,
        "semantic_gold": False,
        "source_universe_frozen": False,
        "source_coverage_ready": False,
        "phase3_complete": False,
        "phase4_blocked": True,
        "material_findings": [],
        "verdict": "PASS",
    }


def _fixture(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> dict[str, Path]:
    pdf_path = tmp_path / "private" / "source.pdf"
    scope_path = tmp_path / "private" / "scope.json"
    jsonl_path = tmp_path / "private" / "converted" / materialization.OUTPUT_FILENAME
    schema_path = tmp_path / "schema.json"
    pdf_payload = b"fixture-pdf"
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
    _write_private(pdf_path, pdf_payload)
    _write_private(scope_path, materialization.canonical_bytes(_scope_review()))
    schema_path.write_text('{"type":"object"}\n', encoding="utf-8")
    monkeypatch.setattr(materialization, "SCHEMA_PATH", schema_path)
    monkeypatch.setattr(materialization.intake, "PDF_SHA256", hashlib.sha256(pdf_payload).hexdigest())
    monkeypatch.setattr(materialization.intake, "PDF_MD5", hashlib.md5(pdf_payload, usedforsecurity=False).hexdigest())
    monkeypatch.setattr(materialization.intake, "PDF_BYTES", len(pdf_payload))
    monkeypatch.setattr(materialization.intake, "PDF_PAGES", len(texts))
    monkeypatch.setattr(materialization.intake, "TEXT_BEARING_PAGES", len(texts))
    monkeypatch.setattr(materialization.intake, "UNICODE_CODE_POINTS", sum(len(text) for text in texts))
    monkeypatch.setattr(materialization.intake, "UTF8_BYTES", sum(len(text.encode("utf-8")) for text in texts))
    monkeypatch.setattr(
        materialization.intake,
        "PAGE_MANIFEST_SHA256",
        hashlib.sha256(b"".join(materialization.canonical_bytes(row) for row in page_rows)).hexdigest(),
    )
    monkeypatch.setattr(
        materialization.intake,
        "EXTRACTED_TEXT_SHA256",
        hashlib.sha256("\n\f\n".join(texts).encode("utf-8")).hexdigest(),
    )

    def fake_reader(path: Path) -> _FakeReader:
        return _FakeReader(path, texts)

    monkeypatch.setattr(materialization, "PdfReader", fake_reader)
    monkeypatch.setattr(materialization.intake, "PdfReader", fake_reader)
    monkeypatch.setattr(materialization, "_validate_bound_public_inputs", lambda **_kwargs: None)
    monkeypatch.setattr(materialization, "_drive_item_id", lambda _path: "fixture-drive-item-id")
    return {
        "pdf": pdf_path,
        "scope": scope_path,
        "jsonl": jsonl_path,
        "schema": schema_path,
    }


def _build(paths: dict[str, Path]) -> dict[str, object]:
    return materialization.build_receipt(
        source_pdf=paths["pdf"],
        scope_review_path=paths["scope"],
        private_jsonl_path=paths["jsonl"],
    )


def test_contract_schema_is_valid_and_text_free() -> None:
    schema_text = materialization.SCHEMA_PATH.read_text(encoding="utf-8")
    Draft202012Validator.check_schema(json.loads(schema_text))
    assert '"text"' not in schema_text
    assert '"source_text"' not in schema_text


def test_materialization_is_deterministic_and_round_trips(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    paths = _fixture(tmp_path, monkeypatch)
    first = _build(paths)
    second = _build(paths)
    assert first == second
    records = materialization.read_private_jsonl(paths["jsonl"])
    assert len(records) == 2
    assert [row["page_start"] for row in records] == [1, 2]
    assert [row["text"] for row in records] == [
        "Перша сторінка українського джерела.",
        "Друга сторінка з теорією.",
    ]
    assert stat.S_IMODE(paths["jsonl"].stat().st_mode) == 0o600
    assert first["gates"]["private_source_units_materialized"] is True  # type: ignore[index]
    assert first["gates"]["database_ingest_authorized"] is False  # type: ignore[index]
    assert first["gates"]["phase4_blocked"] is True  # type: ignore[index]


def test_changed_private_jsonl_is_not_overwritten(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    paths = _fixture(tmp_path, monkeypatch)
    _build(paths)
    paths["jsonl"].write_text('{"changed":true}\n', encoding="utf-8")
    os.chmod(paths["jsonl"], 0o600)
    with pytest.raises(materialization.VspuSourceMaterializationError, match="refusing to overwrite"):
        _build(paths)


def test_non_private_scope_review_is_rejected(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    paths = _fixture(tmp_path, monkeypatch)
    original_stat = Path.stat

    def patched_stat(path: Path, *args: object, **kwargs: object) -> os.stat_result:
        result = original_stat(path, *args, **kwargs)
        if path != paths["scope"]:
            return result
        values = list(result)
        values[0] |= stat.S_IRGRP
        return os.stat_result(values)

    monkeypatch.setattr(Path, "stat", patched_stat)
    with pytest.raises(materialization.VspuSourceMaterializationError, match="mode 0600"):
        _build(paths)


def test_scope_overclaim_is_rejected(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    paths = _fixture(tmp_path, monkeypatch)
    review = _scope_review()
    review["topic_gaps_closed"] = ["phonetics"]
    _write_private(paths["scope"], materialization.canonical_bytes(review))
    with pytest.raises(materialization.VspuSourceMaterializationError, match="closed topic"):
        _build(paths)


def test_scope_block_is_rejected(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    paths = _fixture(tmp_path, monkeypatch)
    review = _scope_review()
    review["verdict"] = "BLOCK"
    _write_private(paths["scope"], materialization.canonical_bytes(review))
    with pytest.raises(materialization.VspuSourceMaterializationError, match="did not pass"):
        _build(paths)


def test_detected_native_text_anomaly_is_rejected(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    paths = _fixture(tmp_path, monkeypatch)
    monkeypatch.setattr(
        materialization,
        "detect_native_text_anomalies",
        lambda _text: {"requires_visual_verification": True},
    )
    with pytest.raises(materialization.VspuSourceMaterializationError, match="requires visual verification"):
        _build(paths)


def test_receipt_tampering_is_rejected(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    paths = _fixture(tmp_path, monkeypatch)
    receipt = _build(paths)
    receipt["gates"]["semantic_gold"] = True  # type: ignore[index]
    receipt["receipt_sha256"] = materialization.receipt_sha256(receipt)
    with pytest.raises(materialization.VspuSourceMaterializationError, match="semantic gold"):
        materialization.validate_receipt(receipt)


@pytest.mark.parametrize(
    "drift_key",
    [
        "candidate_receipt_sha256",
        "university_content_audit_freeze_v1_sha256",
        "complete_source_policy_v4_sha256",
        "historical_periodization_freeze_v1_sha256",
    ],
)
def test_bound_public_input_byte_drift_is_rejected(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, drift_key: str
) -> None:
    paths = {
        "candidate_receipt_sha256": tmp_path / "candidate.json",
        "university_content_audit_freeze_v1_sha256": tmp_path / "university.json",
        "complete_source_policy_v4_sha256": tmp_path / "policy.json",
        "historical_periodization_freeze_v1_sha256": tmp_path / "historical.json",
    }
    candidate = {
        "receipt_sha256": "fixture-receipt",
        "source": {"source_id": materialization.SOURCE_ID},
        "gates": {"scope_critic_complete": False},
    }
    paths["candidate_receipt_sha256"].write_text(json.dumps(candidate), encoding="utf-8")
    for key, path in paths.items():
        if key != "candidate_receipt_sha256":
            path.write_text(f'{{"key":"{key}"}}', encoding="utf-8")
    expected = {
        **materialization.EXPECTED_BINDINGS,
        **{key: materialization.sha256_file(path) for key, path in paths.items()},
    }
    monkeypatch.setattr(materialization, "EXPECTED_BINDINGS", expected)
    monkeypatch.setattr(materialization.intake, "validate_receipt", lambda value: value)
    monkeypatch.setattr(materialization.intake, "receipt_sha256", lambda value: value["receipt_sha256"])
    paths[drift_key].write_text("changed", encoding="utf-8")
    with pytest.raises(materialization.VspuSourceMaterializationError, match=f"{drift_key} byte drift"):
        materialization._validate_bound_public_inputs(
            candidate_path=paths["candidate_receipt_sha256"],
            university_freeze_path=paths["university_content_audit_freeze_v1_sha256"],
            source_policy_path=paths["complete_source_policy_v4_sha256"],
            historical_freeze_path=paths["historical_periodization_freeze_v1_sha256"],
        )


def test_drive_identity_requires_configured_mount_containment(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    cloud_root = tmp_path / "Library" / "CloudStorage"
    (cloud_root / "GoogleDrive-fixture" / "My Drive").mkdir(parents=True)
    outside = tmp_path / "outside.jsonl"
    outside.write_text("fixture", encoding="utf-8")
    monkeypatch.setattr(materialization, "CLOUD_STORAGE_ROOT", cloud_root)
    with pytest.raises(materialization.VspuSourceMaterializationError, match="configured Google Drive mount"):
        materialization._drive_item_id(outside)


def test_drive_identity_requires_provider_xattr(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    cloud_root = tmp_path / "Library" / "CloudStorage"
    inside = cloud_root / "GoogleDrive-fixture" / "My Drive" / "artifact.jsonl"
    inside.parent.mkdir(parents=True)
    inside.write_text("fixture", encoding="utf-8")
    monkeypatch.setattr(materialization, "CLOUD_STORAGE_ROOT", cloud_root)
    monkeypatch.setattr(
        materialization.subprocess,
        "run",
        lambda *_args, **_kwargs: SimpleNamespace(stdout="fixture-provider-id\n"),
    )
    assert materialization._drive_item_id(inside) == "fixture-provider-id"


def test_symlinked_private_inputs_and_outputs_are_rejected(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    paths = _fixture(tmp_path, monkeypatch)
    scope_link = tmp_path / "scope-link.json"
    scope_link.symlink_to(paths["scope"])
    with pytest.raises(materialization.VspuSourceMaterializationError, match="symbolic-link"):
        materialization.validate_scope_review(scope_link)

    pdf_link = tmp_path / "pdf-link.pdf"
    pdf_link.symlink_to(paths["pdf"])
    with pytest.raises(materialization.intake.VspuModernTheoryIntakeError, match="symbolic-link"):
        materialization.extract_records(pdf_link)

    real_private = tmp_path / "real-private"
    real_private.mkdir()
    private_link = tmp_path / "private-link"
    private_link.symlink_to(real_private, target_is_directory=True)
    with pytest.raises(materialization.VspuSourceMaterializationError, match="symbolic-link"):
        materialization.write_private_jsonl(private_link / materialization.OUTPUT_FILENAME, [{"text": "x"}])

    git_root = tmp_path / "git-root"
    (git_root / ".git").mkdir(parents=True)
    real_public = git_root / "real-public"
    real_public.mkdir()
    public_link = git_root / "public-link"
    public_link.symlink_to(real_public, target_is_directory=True)
    with pytest.raises(materialization.VspuSourceMaterializationError, match="symbolic-link"):
        materialization.write_public_receipt(public_link / "receipt.json", {"ok": True})


def test_public_receipt_is_immutable(tmp_path: Path) -> None:
    git_root = tmp_path / "checkout"
    (git_root / ".git").mkdir(parents=True)
    output = git_root / "receipt.json"
    materialization.write_public_receipt(output, {"value": 1})
    materialization.write_public_receipt(output, {"value": 1})
    with pytest.raises(materialization.VspuSourceMaterializationError, match="refusing to overwrite"):
        materialization.write_public_receipt(output, {"value": 2})


def test_check_cli_reports_receipt(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    receipt_path = tmp_path / "receipt.json"
    receipt_path.write_text('{"receipt_sha256":"fixture"}', encoding="utf-8")
    monkeypatch.setattr(materialization, "validate_receipt", lambda value: value)
    assert materialization.main(["--check", str(receipt_path)]) == 0
    assert json.loads(capsys.readouterr().out) == {"ok": True, "receipt_sha256": "fixture"}


def test_output_inside_git_is_rejected(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    paths = _fixture(tmp_path, monkeypatch)
    git_root = tmp_path / "checkout"
    git_root.mkdir()
    (git_root / ".git").mkdir()
    output = git_root / materialization.OUTPUT_FILENAME
    with pytest.raises(materialization.VspuSourceMaterializationError, match="cannot live inside Git"):
        materialization.build_receipt(
            source_pdf=paths["pdf"],
            scope_review_path=paths["scope"],
            private_jsonl_path=output,
        )
