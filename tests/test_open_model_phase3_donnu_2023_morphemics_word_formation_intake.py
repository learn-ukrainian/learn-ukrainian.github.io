"""Hermetic tests for DonNU 2023 morphemics/word-formation source admission."""

from __future__ import annotations

import copy
import json
import os
import stat
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from scripts.projects.open_model_data import phase3_donnu_2023_morphemics_word_formation_intake as intake

PUBLIC_RECEIPT = intake.DEFAULT_PUBLIC_RECEIPT_PATH
SCHEMA = intake.SCHEMA_PATH


def _drive_staging() -> Path | None:
    try:
        return intake.default_staging_root()
    except intake.Donnu2023MorphemicsWordFormationIntakeError:
        return None


def test_contract_schema_is_valid_and_text_free() -> None:
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    schema_text = SCHEMA.read_text(encoding="utf-8")
    assert schema.get("additionalProperties") is False
    assert '"source_text"' not in schema_text
    assert '"page_texts"' not in schema_text
    assert "GoogleDrive-" not in schema_text
    assert "@gmail.com" not in schema_text
    assert "NOTE: PLACE YOUR OWN LICENSE HERE" not in schema_text


def test_mint_is_deterministic_and_preserves_false_completion_gates() -> None:
    first = intake.mint_receipt()
    second = intake.mint_receipt()
    assert first == second
    assert first["status"] == intake.STATUS
    assert first["text_free"] is True
    assert first["provider_calls"] is False
    assert first["review_scope"]["topic_gaps_closed"] == []
    assert first["review_scope"]["topic_gaps_narrowed"] == []
    assert first["content_fitness"]["topic_gaps_narrowed_claimed"] == []
    assert first["content_fitness"]["adversarial_dispositions"]["morphemics"] == "NARROW_ONLY"
    assert first["content_fitness"]["adversarial_dispositions"]["word_formation"] == "NARROW_ONLY"
    assert first["content_fitness"]["adversarial_dispositions"]["semantics"] == "REJECT"
    assert first["content_fitness"]["adversarial_dispositions"]["phraseology"] == "REJECT"
    assert first["rights"]["rights_statement"] == intake.RIGHTS_STATEMENT
    assert first["rights"]["public_redistribution_authorized"] is False
    assert first["rights"]["public_dataset_export_authorized"] is False
    assert first["rights"]["publish_source_text_authorized"] is False
    assert first["rights"]["unrestricted_training_export_authorized"] is False
    assert first["rights"]["reuse_license"] == "reuse_license_not_established"
    assert first["gates"]["semantic_gold"] is False
    assert first["gates"]["database_ingest_authorized"] is False
    assert first["gates"]["topic_gaps_closed"] is False
    assert first["gates"]["topic_gaps_narrowed"] is False
    assert first["gates"]["source_freeze_ready"] is False
    assert first["gates"]["phase3_complete"] is False
    assert first["gates"]["phase4_blocked"] is True
    assert first["denominators"]["v2_source_units"] == 67041
    assert first["denominators"]["v2_evaluation_identities"] == 9392
    assert first["denominators"]["phase3_labels"] == 0
    assert first["denominators"]["cycle002_diagnostic_only"] is True
    assert first["denominators"]["candidate_additive_outside_v2_totals"] is True
    assert first["denominators"]["candidate_source_count"] == 30
    assert first["text_layer"]["page_count_discrepancy"]["recorded_without_correction"] is True
    assert first["text_layer"]["page_count_discrepancy"]["pdf_page_objects"] == 215
    assert first["text_layer"]["page_count_discrepancy"]["catalog_citation_pages"] == 214
    assert first["text_layer"]["empty_text_pages"] == [1]
    assert first["native_exactness"]["flagged_chunk_count"] == 0
    assert first["native_exactness"]["clean_chunk_count"] == 215


def test_public_receipt_is_immutable(tmp_path: Path) -> None:
    receipt = intake.mint_receipt()
    out = tmp_path / "git" / "receipt.json"
    out.parent.mkdir(parents=True)
    (out.parent / ".git").mkdir()
    intake.write_public_receipt(out, receipt)
    assert stat.S_IMODE(out.stat().st_mode) == intake.PRIVATE_FILE_MODE
    intake.write_public_receipt(out, receipt)
    other = dict(receipt)
    other["status"] = "TAMPERED"
    other["receipt_sha256"] = intake.receipt_sha256(other)
    with pytest.raises(intake.Donnu2023MorphemicsWordFormationIntakeError, match="immutable public receipt"):
        intake.write_public_receipt(out, other)


def test_public_receipt_accepts_existing_tracked_checkout_mode(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    receipt = intake.mint_receipt()
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
    assert stat.S_IMODE(out.lstat().st_mode) == intake.TRACKED_PUBLIC_FILE_MODE
    intake.write_public_receipt(out, receipt)
    assert out.read_bytes() == payload


def test_concurrent_receipt_creation_cannot_clobber_winner(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    receipt = intake.mint_receipt()
    out = tmp_path / "git" / "receipt.json"
    out.parent.mkdir(parents=True)
    (out.parent / ".git").mkdir()

    def concurrent_link(source: Path, destination: Path, *, follow_symlinks: bool = True) -> None:
        out.write_bytes(b'{"winner":true}\n')
        os.chmod(out, 0o600)
        raise FileExistsError

    monkeypatch.setattr(os, "link", concurrent_link)
    with pytest.raises(intake.Donnu2023MorphemicsWordFormationIntakeError, match="immutable public receipt"):
        intake.write_public_receipt(out, receipt)
    assert out.read_bytes() == b'{"winner":true}\n'


def test_validate_receipt_rebinds_university_freeze_and_policy(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    receipt = intake.mint_receipt()
    intake.validate_receipt(receipt)

    tampered_freeze = tmp_path / "freeze.json"
    tampered_freeze.write_bytes(b'{"tampered":true}\n')
    monkeypatch.setattr(intake, "UNIVERSITY_FREEZE_PATH", tampered_freeze)
    with pytest.raises(intake.Donnu2023MorphemicsWordFormationIntakeError, match="university content-audit freeze"):
        intake.validate_receipt(receipt)

    monkeypatch.setattr(
        intake, "UNIVERSITY_FREEZE_PATH", intake.DATA / "admission/phase3_university_content_audit_freeze_v1.json"
    )
    tampered_policy = tmp_path / "policy.json"
    tampered_policy.write_bytes(b'{"tampered":true}\n')
    monkeypatch.setattr(intake, "SOURCE_POLICY_PATH", tampered_policy)
    with pytest.raises(intake.Donnu2023MorphemicsWordFormationIntakeError, match="complete source policy v4"):
        intake.validate_receipt(receipt)


def test_validate_receipt_rejects_overclaims() -> None:
    receipt = intake.mint_receipt()
    receipt["review_scope"]["topic_gaps_closed"] = ["morphemics"]
    receipt["receipt_sha256"] = intake.receipt_sha256(receipt)
    with pytest.raises(intake.Donnu2023MorphemicsWordFormationIntakeError, match=r"closed topic gap|schema violation"):
        intake.validate_receipt(receipt)

    receipt = intake.mint_receipt()
    receipt["gates"]["semantic_gold"] = True
    receipt["receipt_sha256"] = intake.receipt_sha256(receipt)
    with pytest.raises(intake.Donnu2023MorphemicsWordFormationIntakeError, match=r"semantic gold|schema violation"):
        intake.validate_receipt(receipt)

    receipt = intake.mint_receipt()
    receipt["content_fitness"]["adversarial_dispositions"]["semantics"] = "NARROW_ONLY"
    receipt["receipt_sha256"] = intake.receipt_sha256(receipt)
    with pytest.raises(
        intake.Donnu2023MorphemicsWordFormationIntakeError, match=r"semantics disposition|schema violation"
    ):
        intake.validate_receipt(receipt)


@pytest.mark.parametrize(
    ("path", "forged_value", "match"),
    [
        (("bindings", "private_jsonl_sha256"), "0" * 64, r"private JSONL hash drift|schema violation"),
        (("bindings", "private_jsonl_bytes"), 1, r"private JSONL byte denominator drift|schema violation"),
        (("bindings", "exactness_audit_sha256"), "0" * 64, r"exactness audit hash drift|schema violation"),
        (("bindings", "content_fit_audit_sha256"), "0" * 64, r"content-fit audit hash drift|schema violation"),
        (("bindings", "custody_receipt_file_sha256"), "0" * 64, r"custody receipt file hash drift|schema violation"),
        (("bindings", "custody_receipt_body_sha256"), "0" * 64, r"custody receipt body hash drift|schema violation"),
        (("bindings", "source_pdf_sha256"), "0" * 64, r"receipt PDF hash drift|schema violation"),
        (("bindings", "checksums_sha256"), "0" * 64, r"SHA256SUMS hash drift|schema violation"),
        (("bindings", "license_text_sha256"), "0" * 64, r"license text hash drift|schema violation"),
        (
            ("native_exactness", "audit_receipt_sha256"),
            "0" * 64,
            r"native exactness audit receipt hash drift|schema violation",
        ),
        (("denominators", "v2_source_units"), 1, r"v2 source-unit denominator drift|schema violation"),
        (("denominators", "v2_evaluation_identities"), 1, r"v2 evaluation denominator drift|schema violation"),
        (("denominators", "cycle002_diagnostic_only"), False, r"Cycle002 diagnostic-only drift|schema violation"),
        (("source", "isbn"), "000-0-000-00000-0", r"source ISBN drift|schema violation"),
        (("source", "item_url"), "https://example.invalid/item", r"source item locator drift|schema violation"),
        (
            ("text_layer", "page_count_discrepancy", "recorded_without_correction"),
            False,
            r"page-count discrepancy must remain recorded|schema violation",
        ),
        (("rights", "public_redistribution_authorized"), True, r"redistribution|schema violation"),
        (("rights", "unrestricted_training_export_authorized"), True, r"training export|schema violation"),
        (("gates", "phase3_complete"), True, r"Phase 3 completion|schema violation"),
        (("gates", "phase4_blocked"), False, r"Phase 4|schema violation"),
        (("gates", "source_freeze_ready"), True, r"source freeze readiness|schema violation"),
        (("gates", "topic_gaps_narrowed"), True, r"topic gap narrowing|schema violation"),
        *(
            (
                ("custody", "google_drive_provider_identity_sha256", field),
                "0" * 64,
                r"google drive provider identity mapping drift|schema violation",
            )
            for field in sorted(intake.AUTHORITATIVE_GOOGLE_DRIVE_PROVIDER_IDENTITY_SHA256)
        ),
    ],
)
def test_validate_receipt_rejects_resealed_authoritative_mutations(
    path: tuple[str, ...], forged_value: object, match: str
) -> None:
    if not PUBLIC_RECEIPT.is_file():
        pytest.skip("public receipt not materialized yet")
    receipt = json.loads(PUBLIC_RECEIPT.read_text(encoding="utf-8"))
    forged = copy.deepcopy(receipt)
    cursor: dict[str, object] = forged
    for key in path[:-1]:
        nested = cursor[key]
        assert isinstance(nested, dict)
        cursor = nested
    cursor[path[-1]] = forged_value
    forged["receipt_sha256"] = intake.receipt_sha256(forged)
    with pytest.raises(intake.Donnu2023MorphemicsWordFormationIntakeError, match=match):
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
    assert validated["native_exactness"]["audit_receipt_sha256"] == intake.EXACTNESS_AUDIT_SHA256
    assert validated["bindings"]["content_fit_audit_sha256"] == intake.CONTENT_FIT_AUDIT_SHA256
    assert validated["bindings"]["custody_receipt_file_sha256"] == intake.CUSTODY_RECEIPT_FILE_SHA256
    assert validated["bindings"]["custody_receipt_body_sha256"] == intake.CUSTODY_RECEIPT_BODY_SHA256
    assert validated["bindings"]["checksums_sha256"] == intake.CHECKSUMS_SHA256
    assert validated["bindings"]["university_content_audit_freeze_v1_sha256"] == intake.UNIVERSITY_FREEZE_SHA256
    assert validated["bindings"]["complete_source_policy_v4_sha256"] == intake.SOURCE_POLICY_SHA256
    assert (
        validated["custody"]["google_drive_provider_identity_sha256"]
        == intake.AUTHORITATIVE_GOOGLE_DRIVE_PROVIDER_IDENTITY_SHA256
    )
    assert validated["native_exactness"]["flagged_chunk_count"] == 0
    assert validated["review_scope"]["topic_gaps_narrowed"] == []
    assert validated["rights"]["rights_statement"] == intake.RIGHTS_STATEMENT
    assert validated["gates"]["phase3_complete"] is False
    assert validated["gates"]["phase4_blocked"] is True
    dumped = json.dumps(validated, ensure_ascii=False)
    assert "GoogleDrive-" not in dumped
    assert "@gmail.com" not in dumped
    assert "\f" not in dumped
    assert "NOTE: PLACE YOUR OWN LICENSE HERE" not in dumped
    assert "page_texts" not in validated


def test_check_cli_is_hermetic_without_drive(monkeypatch: pytest.MonkeyPatch) -> None:
    if not PUBLIC_RECEIPT.is_file():
        pytest.skip("public receipt not materialized yet")

    def boom() -> Path:
        raise intake.Donnu2023MorphemicsWordFormationIntakeError("drive must not be touched")

    monkeypatch.setattr(intake, "default_staging_root", boom)
    assert intake.main(["--check", str(PUBLIC_RECEIPT)]) == 0


def test_no_db_mutation_surface() -> None:
    source = Path(intake.__file__).read_text(encoding="utf-8")
    assert "sources.db" not in source
    assert "sqlite3" not in source
    assert "INSERT INTO" not in source


def test_private_audit_against_drive_custody() -> None:
    drive_staging = _drive_staging()
    if drive_staging is None:
        pytest.skip("configured Drive mount unavailable")
    required = [
        drive_staging / intake.PDF_FILENAME,
        drive_staging / intake.LANDING_FILENAME,
        drive_staging / intake.ITEM_METADATA_FILENAME,
        drive_staging / intake.BITSTREAM_METADATA_FILENAME,
        drive_staging / intake.LICENSE_TEXT_FILENAME,
        drive_staging / "processed" / "grade-00" / intake.JSONL_FILENAME,
        drive_staging / "exactness" / intake.EXACTNESS_AUDIT_FILENAME,
        drive_staging / intake.CONTENT_FIT_AUDIT_FILENAME,
        drive_staging / intake.CUSTODY_RECEIPT_FILENAME,
        drive_staging / intake.CHECKSUMS_FILENAME,
    ]
    if not all(path.exists() for path in required):
        pytest.skip("Drive custody artifacts unavailable")
    result = intake.private_audit(drive_staging)
    assert result["ok"] is True
    assert result["checksum_entries"] == 13
    assert result["custody_receipt_body_sha256"] == intake.CUSTODY_RECEIPT_BODY_SHA256
    assert result["provider_identity_sha256"] == intake.AUTHORITATIVE_GOOGLE_DRIVE_PROVIDER_IDENTITY_SHA256
