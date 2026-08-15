"""Hermetic tests for the text-free LNU 2024 phonetics/phonology source intake."""

from __future__ import annotations

import copy
import json
import os
import stat
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

import pytest
from jsonschema import Draft202012Validator

from scripts.projects.open_model_data import phase3_lnu_2024_phonetics_phonology_intake as intake


def _private(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    os.chmod(path.parent, 0o700)
    path.write_bytes(payload)
    os.chmod(path, 0o600)


def _staging(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    stage = tmp_path / "private" / "stage"
    stage.mkdir(parents=True)
    os.chmod(stage, 0o700)
    artifacts = {}
    identifiers: dict[str, str] = {}
    for label, (filename, _, _, _) in intake.ARTIFACTS.items():
        payload = f"synthetic-{label}".encode()
        _private(stage / filename, payload)
        identity = f"synthetic-{label}-identity"
        identifiers[label] = identity
        artifacts[label] = (
            filename,
            len(payload),
            intake.sha256_bytes(payload),
            intake.sha256_bytes(identity.encode()),
        )
    monkeypatch.setattr(intake, "ARTIFACTS", artifacts)
    monkeypatch.setattr(
        intake, "_drive_item_id", lambda path: identifiers[next(k for k, v in artifacts.items() if path.name == v[0])]
    )
    return stage


def test_schema_is_strict_and_text_free() -> None:
    schema = json.loads(intake.SCHEMA_PATH.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    text = intake.SCHEMA_PATH.read_text(encoding="utf-8")
    assert schema["additionalProperties"] is False
    assert '"source_text"' not in text and '"page_texts"' not in text
    assert "GoogleDrive-" not in text and "/Users/" not in text

    def assert_closed(value: object) -> None:
        if isinstance(value, dict):
            if value.get("type") == "object":
                assert value.get("additionalProperties") is False
            for nested in value.values():
                assert_closed(nested)
        elif isinstance(value, list):
            for nested in value:
                assert_closed(nested)

    assert_closed(schema)


def test_mint_is_source_blind_deterministic_and_fail_closed() -> None:
    first, second = intake.mint_receipt(), intake.mint_receipt()
    assert first == second
    assert first["provider_calls"] is False and first["text_free"] is True
    assert first["denominators"] == {
        "v2_source_units": 67041,
        "v2_evaluation_identities": 9392,
        "university_total": 26,
        "university_sufficient": 5,
        "university_partial": 21,
        "university_missing": 0,
        "candidate_sources": 30,
        "database_resident_sources": 20,
        "reference_only_sources": 6,
        "quarantine_sources": 4,
    }
    assert [cell["area"] for cell in first["content_fitness"]["target_cells"]] == list(intake.TARGETS)
    assert all(cell["evidence_classification"] == "NARROW_ONLY" for cell in first["content_fitness"]["target_cells"])
    assert "target_cell" not in first["content_fitness"]
    assert first["content_fitness"]["topic_gaps_closed"] == []
    assert first["content_fitness"]["topic_gaps_narrowed_claimed"] == []
    assert first["gates"]["phase4_blocked"] is True and first["gates"]["phase4_authorized"] is False
    encoded = intake.canonical_json(first)
    assert all(
        value not in encoded for value in ("GoogleDrive-", "@gmail.com", "/Users/", '"page_texts"', '"source_text"')
    )


@pytest.mark.parametrize(
    "path,value",
    [
        (("content_fitness", "limitations"), "forged narrative"),
        (("content_fitness", "target_cells", 0, "qualified_source_needed"), "forged rationale"),
        (("content_fitness", "descriptive_topics", 0, "role"), "forged secondary role"),
        (("rights", "unrestricted_training_export"), True),
        (("signals", "spectrograph"), 9),
        (("text_layer", "extracted_characters"), 1),
        (("source", "year"), 2023),
        (("custody", "artifacts", "source_pdf", "provider_item_id_sha256"), "0" * 64),
        (("gates", "database_ingest_authorized"), True),
        (("gates", "semantic_gold"), True),
        (("gates", "author_eval_membership"), True),
        (("gates", "topic_gaps_closed"), True),
        (("gates", "topic_gaps_narrowed"), True),
        (("gates", "source_universe_frozen"), True),
        (("gates", "source_coverage_ready"), True),
        (("gates", "source_freeze_ready"), True),
        (("gates", "phase3_complete"), True),
        (("gates", "phase4_authorized"), True),
        (("gates", "phase4_blocked"), False),
    ],
)
def test_resealed_mutations_fail(path: tuple[object, ...], value: object) -> None:
    receipt = copy.deepcopy(intake.mint_receipt())
    cursor: object = receipt
    for key in path[:-1]:
        cursor = cursor[key]  # type: ignore[index]
    cursor[path[-1]] = value  # type: ignore[index]
    receipt["receipt_sha256"] = intake.receipt_sha256(receipt)
    with pytest.raises(intake.Lnu2024PhoneticsPhonologyIntakeError, match=r"body drift|schema violation"):
        intake.validate_receipt(receipt)


def test_private_audit_rejects_modes_symlink_and_hash_drift(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    stage = _staging(tmp_path, monkeypatch)
    first = next(iter(intake.ARTIFACTS.values()))[0]
    os.chmod(stage, 0o600)
    with pytest.raises(intake.Lnu2024PhoneticsPhonologyIntakeError, match="0700"):
        intake.private_audit(stage)
    os.chmod(stage, 0o700)
    os.chmod(stage / first, 0o400)
    with pytest.raises(intake.Lnu2024PhoneticsPhonologyIntakeError, match="0600"):
        intake.private_audit(stage)
    os.chmod(stage / first, 0o600)
    (stage / first).write_bytes(b"drift")
    with pytest.raises(intake.Lnu2024PhoneticsPhonologyIntakeError, match=r"byte drift|hash drift"):
        intake.private_audit(stage)
    stage = _staging(tmp_path / "symlink", monkeypatch)
    (stage / "linked").symlink_to(next(iter(intake.ARTIFACTS.values()))[0])
    label, values = next(iter(intake.ARTIFACTS.items()))
    monkeypatch.setattr(intake, "ARTIFACTS", {**intake.ARTIFACTS, label: ("linked", *values[1:])})
    with pytest.raises(intake.Lnu2024PhoneticsPhonologyIntakeError, match=r"symbolic-link|regular file"):
        intake.private_audit(stage)


def test_private_audit_rejects_relative_ancestor_symlink(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    real_root = tmp_path / "real-root"
    _staging(real_root, monkeypatch)
    (tmp_path / "alias").symlink_to(real_root, target_is_directory=True)
    monkeypatch.chdir(tmp_path)

    with pytest.raises(intake.Lnu2024PhoneticsPhonologyIntakeError, match="symbolic-link path component"):
        intake.private_audit(Path("alias/private/stage"))


def test_private_audit_rejects_provider_identity_drift(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    stage = _staging(tmp_path, monkeypatch)
    monkeypatch.setattr(intake, "_drive_item_id", lambda path: "forged-provider-identity")
    with pytest.raises(intake.Lnu2024PhoneticsPhonologyIntakeError, match="provider identity drift"):
        intake.private_audit(stage)


def test_private_audit_rejects_missing_receipt(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    stage = _staging(tmp_path, monkeypatch)
    receipt_name = intake.ARTIFACTS["private_audit_receipt"][0]
    (stage / receipt_name).unlink()
    with pytest.raises(intake.Lnu2024PhoneticsPhonologyIntakeError, match="missing private_audit_receipt"):
        intake.private_audit(stage)


def test_private_audit_rejects_xattr_timeout(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    drive_root = tmp_path / "GoogleDrive-fake"
    (drive_root / "My Drive").mkdir(parents=True)
    monkeypatch.setattr(intake, "CLOUD_STORAGE_ROOT", tmp_path)
    stage = drive_root / "My Drive" / "Projects" / "learn-ukrainian-data" / "stage"
    stage.mkdir(parents=True)
    os.chmod(stage, 0o700)
    artifacts = {}
    for label, (filename, _, _, _) in intake.ARTIFACTS.items():
        payload = f"synthetic-{label}".encode()
        _private(stage / filename, payload)
        artifacts[label] = (
            filename,
            len(payload),
            intake.sha256_bytes(payload),
            intake.sha256_bytes(f"synthetic-{label}-identity".encode()),
        )
    monkeypatch.setattr(intake, "ARTIFACTS", artifacts)

    def timeout_run(*args: object, **kwargs: object) -> subprocess.CompletedProcess[str]:
        raise subprocess.TimeoutExpired(cmd=["xattr"], timeout=intake.DRIVE_XATTR_TIMEOUT_SECONDS)

    monkeypatch.setattr(intake.subprocess, "run", timeout_run)
    with pytest.raises(intake.Lnu2024PhoneticsPhonologyIntakeError, match="provider identity"):
        intake.private_audit(stage)


def test_private_audit_synthetic_and_cli(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    result = intake.private_audit(_staging(tmp_path, monkeypatch))
    assert result["ok"] is True and result["artifact_count"] == 5 and "/Users/" not in intake.canonical_json(result)
    out = tmp_path / "git" / "receipt.json"
    out.parent.mkdir()
    (out.parent / ".git").mkdir()
    mint = subprocess.run(
        [sys.executable, str(intake.SCRIPT_PATH), "--mint", "--write", str(out)],
        capture_output=True,
        text=True,
        timeout=30,
    )
    check = subprocess.run(
        [sys.executable, str(intake.SCRIPT_PATH), "--check", str(out)], capture_output=True, text=True, timeout=30
    )
    assert mint.returncode == check.returncode == 0, mint.stdout + mint.stderr + check.stdout + check.stderr
    assert json.loads(mint.stdout)["receipt_sha256"] == json.loads(check.stdout)["receipt_sha256"]
    assert stat.S_IMODE(out.stat().st_mode) == 0o600


def test_immutable_public_receipt_and_no_db_surface(tmp_path: Path) -> None:
    out = tmp_path / "git" / "receipt.json"
    out.parent.mkdir()
    (out.parent / ".git").mkdir()
    receipt = intake.mint_receipt()
    intake.write_public_receipt(out, receipt)
    intake.write_public_receipt(out, receipt)
    forged = {**receipt, "status": "forged"}
    with pytest.raises(intake.Lnu2024PhoneticsPhonologyIntakeError, match="immutable"):
        intake.write_public_receipt(out, forged)
    source = intake.SCRIPT_PATH.read_text(encoding="utf-8")
    assert all(token not in source for token in ("sources.db", "sqlite3", "INSERT INTO"))


def test_materialized_receipt_validates() -> None:
    if not intake.DEFAULT_PUBLIC_RECEIPT_PATH.is_file():
        pytest.skip("receipt has not been materialized")
    receipt = intake.validate_receipt(json.loads(intake.DEFAULT_PUBLIC_RECEIPT_PATH.read_text(encoding="utf-8")))
    assert receipt["receipt_sha256"] == intake.receipt_sha256(receipt)


def test_repeated_mint_and_check_are_byte_identical(tmp_path: Path) -> None:
    out = tmp_path / "git" / "receipt.json"
    out.parent.mkdir()
    (out.parent / ".git").mkdir()
    for _ in range(2):
        receipt = intake.mint_receipt()
        intake.write_public_receipt(out, receipt)
        checked = intake.validate_receipt(json.loads(out.read_text(encoding="utf-8")))
        assert out.read_bytes() == intake.canonical_bytes(checked)


def test_optional_live_drive_audit() -> None:
    try:
        stage = intake.default_staging_root()
    except intake.Lnu2024PhoneticsPhonologyIntakeError:
        pytest.skip("configured Drive mount unavailable")
    if not all((stage / values[0]).is_file() for values in intake.ARTIFACTS.values()):
        pytest.skip("private Drive packet unavailable")
    result = intake.private_audit(stage)
    assert result["ok"] is True
    assert set(result["provider_identity_sha256"]) == set(intake.ARTIFACTS)
    serialized = intake.canonical_json(result)
    assert "provider_item_id" not in serialized
    with patch.object(intake, "_drive_item_id", return_value="live-id"):
        with pytest.raises(intake.Lnu2024PhoneticsPhonologyIntakeError, match="provider identity drift"):
            intake.private_audit(stage)
