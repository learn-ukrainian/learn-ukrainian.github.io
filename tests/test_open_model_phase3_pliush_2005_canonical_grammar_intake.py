"""Hermetic tests for Pliush 2005 canonical-grammar source admission."""

from __future__ import annotations

import copy
import json
import os
import stat
import subprocess
import sys
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from scripts.projects.open_model_data import phase3_pliush_2005_canonical_grammar_intake as intake

PUBLIC_RECEIPT = intake.DEFAULT_PUBLIC_RECEIPT_PATH
SCHEMA = intake.SCHEMA_PATH


def _drive_staging() -> Path | None:
    try:
        return intake.default_staging_root()
    except intake.Pliush2005CanonicalGrammarIntakeError:
        return None


def _write_private(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    os.chmod(path.parent, 0o700)
    path.write_bytes(payload)
    os.chmod(path, 0o600)


def _synthetic_staging(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    staging = tmp_path / "private" / "staging"
    staging.mkdir(parents=True)
    os.chmod(staging, 0o700)
    (staging / "source").mkdir()
    (staging / "metadata").mkdir()
    os.chmod(staging / "source", 0o700)
    os.chmod(staging / "metadata", 0o700)

    payloads = {
        intake.PDF_FILENAME: b"synthetic-pliush-pdf",
        intake.ITEM_HTML_FILENAME: b"<html>synthetic-item</html>",
        intake.ONLINE_BOOK_HTML_FILENAME: b"<html>synthetic-online-book</html>",
        intake.PDF_HEADERS_FILENAME: b"HTTP/1.1 200 OK\n\n",
        intake.ITEM_HEADERS_FILENAME: b"HTTP/1.1 200 OK\n\n",
        intake.ONLINE_BOOK_HEADERS_FILENAME: b"HTTP/1.1 200 OK\n\n",
    }
    sha_map: dict[str, str] = {}
    size_map: dict[str, int] = {}
    for rel, payload in payloads.items():
        path = staging / rel
        _write_private(path, payload)
        digest = intake.sha256_bytes(payload)
        sha_map[rel] = digest
        size_map[rel] = len(payload)

    monkeypatch.setattr(intake, "PDF_SHA256", sha_map[intake.PDF_FILENAME])
    monkeypatch.setattr(intake, "PDF_MD5", "0" * 32)
    monkeypatch.setattr(intake, "PDF_BYTES", size_map[intake.PDF_FILENAME])
    monkeypatch.setattr(intake, "ITEM_HTML_SHA256", sha_map[intake.ITEM_HTML_FILENAME])
    monkeypatch.setattr(intake, "ITEM_HTML_BYTES", size_map[intake.ITEM_HTML_FILENAME])
    monkeypatch.setattr(intake, "ONLINE_BOOK_HTML_SHA256", sha_map[intake.ONLINE_BOOK_HTML_FILENAME])
    monkeypatch.setattr(intake, "ONLINE_BOOK_HTML_BYTES", size_map[intake.ONLINE_BOOK_HTML_FILENAME])
    monkeypatch.setattr(intake, "PDF_HEADERS_SHA256", sha_map[intake.PDF_HEADERS_FILENAME])
    monkeypatch.setattr(intake, "PDF_HEADERS_BYTES", size_map[intake.PDF_HEADERS_FILENAME])
    monkeypatch.setattr(intake, "ITEM_HEADERS_SHA256", sha_map[intake.ITEM_HEADERS_FILENAME])
    monkeypatch.setattr(intake, "ITEM_HEADERS_BYTES", size_map[intake.ITEM_HEADERS_FILENAME])
    monkeypatch.setattr(intake, "ONLINE_BOOK_HEADERS_SHA256", sha_map[intake.ONLINE_BOOK_HEADERS_FILENAME])
    monkeypatch.setattr(intake, "ONLINE_BOOK_HEADERS_BYTES", size_map[intake.ONLINE_BOOK_HEADERS_FILENAME])

    provider_ids = {
        "item_html": "synthetic-item-id",
        "item_response_headers": "synthetic-item-headers-id",
        "online_book_html": "synthetic-online-id",
        "online_book_response_headers": "synthetic-online-headers-id",
        "pdf_response_headers": "synthetic-pdf-headers-id",
        "source_pdf": "synthetic-pdf-id",
    }
    provider_sha = {
        name: intake.sha256_bytes(value.encode("utf-8")) for name, value in sorted(provider_ids.items())
    }
    monkeypatch.setattr(intake, "AUTHORITATIVE_GOOGLE_DRIVE_PROVIDER_IDENTITY_SHA256", provider_sha)

    def fake_verify(path: Path, expected_sha256: str) -> str:
        assert intake.sha256_file(path) == expected_sha256
        label = None
        for key, rel in intake.CUSTODY_ARTIFACTS.items():
            if path == staging / rel:
                label = key
                break
        assert label is not None
        return provider_ids[label]

    monkeypatch.setattr(intake, "_verify_drive_readback", fake_verify)
    monkeypatch.setattr(intake, "default_staging_root", lambda: staging)
    return staging


def test_contract_schema_is_valid_and_text_free() -> None:
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    schema_text = SCHEMA.read_text(encoding="utf-8")
    assert schema.get("additionalProperties") is False
    assert '"source_text"' not in schema_text
    assert '"page_texts"' not in schema_text
    assert "GoogleDrive-" not in schema_text
    assert "@gmail.com" not in schema_text
    assert "/Users/" not in schema_text


def test_mint_is_deterministic_and_preserves_fail_closed_gates() -> None:
    first = intake.mint_receipt()
    second = intake.mint_receipt()
    assert first == second
    assert first["status"] == intake.STATUS
    assert first["text_free"] is True
    assert first["provider_calls"] is False
    assert first["page_map"]["morphemics"]["pdf_start"] == 8
    assert first["page_map"]["morphemics"]["printed_start"] == 7
    assert first["page_map"]["word_formation"]["pdf_start"] == 21
    assert first["page_map"]["word_formation"]["printed_end"] == 68
    assert first["page_map"]["morphology_main_body"]["pdf_start"] == 70
    assert first["page_map"]["abbreviations"]["pdf_end"] == 282
    assert first["page_map"]["contents"]["pdf_start"] == 283
    assert first["page_map"]["colophon_pdf_page"] == 289
    assert first["visual_qa"]["passed_pdf_pages"] == [3, 8, 21, 70, 283, 289]
    assert first["content_fitness"]["topic_gaps_closed"] == []
    assert first["content_fitness"]["topic_gaps_narrowed_claimed"] == []
    assert first["content_fitness"]["audience"]["publication_period_post_2019"] is False
    assert first["content_fitness"]["audience"]["publication_year"] == 2005
    assert first["content_fitness"]["cells"]["morphemics"]["role"] == "canonical_theory_corroboration"
    assert first["content_fitness"]["cells"]["word_formation"]["disposition"] == "NARROW_ONLY"
    assert first["content_fitness"]["secondary_observation_cells"]["morphology"]["role"] == "secondary_corroboration"
    assert first["source"]["work_isbn"] == "966-642-264-6"
    assert first["source"]["part_1_isbn"] == "966-642-263-8"
    assert first["source"]["isbn_roles_recorded"] is True
    assert first["rights"]["nbuv_terms"] == intake.NBUV_TERMS
    assert first["rights"]["private_acquisition"] is True
    assert first["rights"]["private_audit"] is True
    assert first["rights"]["private_training_preparation"] is True
    assert first["rights"]["public_full_text_export"] is False
    assert first["rights"]["unrestricted_training_export"] is False
    assert first["gates"]["database_ingest_authorized"] is False
    assert first["gates"]["semantic_gold"] is False
    assert first["gates"]["phase3_complete"] is False
    assert first["gates"]["phase4_blocked"] is True
    assert first["denominators"]["v2_source_units"] == 67041
    assert first["denominators"]["v2_evaluation_identities"] == 9392
    dumped = intake.canonical_json(first)
    assert "GoogleDrive-" not in dumped
    assert "@gmail.com" not in dumped
    assert "/Users/" not in dumped
    assert "Library/CloudStorage" not in dumped


def test_exact_page_map_boundaries() -> None:
    receipt = intake.mint_receipt()
    assert receipt["page_map"] == intake.PAGE_MAP
    assert receipt["page_map"]["body_mapping_rule"] == "pdf_object_equals_printed_page_plus_one"
    assert receipt["page_map"]["prior_advisory_off_by_one_corrected"] is True
    assert receipt["source"]["title_imprint_pages"] == 286
    assert receipt["source"]["nbuv_presentation_pages"] == 288
    assert receipt["source"]["pages"] == 289


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
    with pytest.raises(intake.Pliush2005CanonicalGrammarIntakeError, match="immutable public receipt"):
        intake.write_public_receipt(out, other)


def test_validate_receipt_rebinds_university_freeze_and_policy(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    receipt = intake.mint_receipt()
    intake.validate_receipt(receipt)

    tampered_freeze = tmp_path / "freeze.json"
    tampered_freeze.write_bytes(b'{"tampered":true}\n')
    monkeypatch.setattr(intake, "UNIVERSITY_FREEZE_PATH", tampered_freeze)
    with pytest.raises(intake.Pliush2005CanonicalGrammarIntakeError, match="university content-audit freeze"):
        intake.validate_receipt(receipt)

    monkeypatch.setattr(
        intake, "UNIVERSITY_FREEZE_PATH", intake.DATA / "admission/phase3_university_content_audit_freeze_v1.json"
    )
    tampered_policy = tmp_path / "policy.json"
    tampered_policy.write_bytes(b'{"tampered":true}\n')
    monkeypatch.setattr(intake, "SOURCE_POLICY_PATH", tampered_policy)
    with pytest.raises(intake.Pliush2005CanonicalGrammarIntakeError, match="complete source policy v4"):
        intake.validate_receipt(receipt)


def test_validate_receipt_rejects_overclaims() -> None:
    receipt = intake.mint_receipt()
    receipt["review_scope"]["topic_gaps_closed"] = ["morphemics"]
    receipt["receipt_sha256"] = intake.receipt_sha256(receipt)
    with pytest.raises(intake.Pliush2005CanonicalGrammarIntakeError, match=r"closed topic gap|schema violation"):
        intake.validate_receipt(receipt)

    receipt = intake.mint_receipt()
    receipt["content_fitness"]["topic_gaps_narrowed_claimed"] = ["word_formation"]
    receipt["receipt_sha256"] = intake.receipt_sha256(receipt)
    with pytest.raises(intake.Pliush2005CanonicalGrammarIntakeError, match=r"narrowing|schema violation"):
        intake.validate_receipt(receipt)

    receipt = intake.mint_receipt()
    receipt["content_fitness"]["audience"]["publication_period_post_2019"] = True
    receipt["receipt_sha256"] = intake.receipt_sha256(receipt)
    with pytest.raises(intake.Pliush2005CanonicalGrammarIntakeError, match=r"post-2019|schema violation"):
        intake.validate_receipt(receipt)

    receipt = intake.mint_receipt()
    receipt["source"]["year"] = 2019
    receipt["receipt_sha256"] = intake.receipt_sha256(receipt)
    with pytest.raises(intake.Pliush2005CanonicalGrammarIntakeError, match=r"publication year|schema violation"):
        intake.validate_receipt(receipt)

    receipt = intake.mint_receipt()
    receipt["rights"]["public_full_text_export"] = True
    receipt["receipt_sha256"] = intake.receipt_sha256(receipt)
    with pytest.raises(intake.Pliush2005CanonicalGrammarIntakeError, match=r"full-text export|schema violation"):
        intake.validate_receipt(receipt)

    receipt = intake.mint_receipt()
    receipt["gates"]["database_ingest_authorized"] = True
    receipt["receipt_sha256"] = intake.receipt_sha256(receipt)
    with pytest.raises(intake.Pliush2005CanonicalGrammarIntakeError, match=r"database ingest|schema violation"):
        intake.validate_receipt(receipt)

    receipt = intake.mint_receipt()
    receipt["gates"]["phase3_complete"] = True
    receipt["receipt_sha256"] = intake.receipt_sha256(receipt)
    with pytest.raises(intake.Pliush2005CanonicalGrammarIntakeError, match=r"Phase 3 completion|schema violation"):
        intake.validate_receipt(receipt)

    receipt = intake.mint_receipt()
    receipt["content_fitness"]["cells"]["morphemics"]["role"] = "current_source_closure"
    receipt["receipt_sha256"] = intake.receipt_sha256(receipt)
    with pytest.raises(intake.Pliush2005CanonicalGrammarIntakeError, match=r"role expansion|schema violation"):
        intake.validate_receipt(receipt)


@pytest.mark.parametrize(
    ("path", "forged_value", "match"),
    [
        (("bindings", "source_pdf_sha256"), "0" * 64, r"receipt PDF hash drift|schema violation"),
        (("bindings", "item_html_sha256"), "0" * 64, r"item HTML hash drift|schema violation"),
        (("bindings", "online_book_html_sha256"), "0" * 64, r"online-book HTML hash drift|schema violation"),
        (("denominators", "v2_source_units"), 1, r"v2 source-unit denominator drift|schema violation"),
        (("denominators", "v2_evaluation_identities"), 1, r"v2 evaluation denominator drift|schema violation"),
        (("source", "work_isbn"), "000-0-000-00000-0", r"work ISBN drift|schema violation"),
        (("source", "part_1_isbn"), "000-0-000-00000-0", r"Part I ISBN drift|schema violation"),
        (("native_exactness", "production_eligible_note"), "forged", r"receipt body drift"),
        (("content_fitness", "document_profile", "printed_page_offset_note"), "forged", r"receipt body drift"),
        (("content_fitness", "explicit_limitations"), ["forged"], r"receipt body drift"),
        (
            ("content_fitness", "secondary_observation_cells", "morphology", "rationale_codes"),
            ["forged"],
            r"receipt body drift",
        ),
        (("residuals",), ["forged"], r"receipt body drift"),
        (
            ("content_fitness", "cells", "morphemics", "qualified_source_needed"),
            "forged",
            r"receipt body drift",
        ),
        (("content_fitness", "cells", "word_formation", "rationale_codes"), ["forged"], r"receipt body drift"),
        (("page_map", "morphemics", "pdf_start"), 7, r"page map drift|schema violation|morphemics page-map"),
        (("rights", "unrestricted_training_export"), True, r"training export|schema violation"),
        (("gates", "phase4_blocked"), False, r"Phase 4|schema violation"),
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
    receipt = intake.mint_receipt()
    forged = copy.deepcopy(receipt)
    cursor: dict[str, object] = forged
    for key in path[:-1]:
        nested = cursor[key]
        assert isinstance(nested, dict)
        cursor = nested
    cursor[path[-1]] = forged_value
    forged["receipt_sha256"] = intake.receipt_sha256(forged)
    with pytest.raises(intake.Pliush2005CanonicalGrammarIntakeError, match=match):
        intake.validate_receipt(forged)


def test_private_audit_rejects_symlink_and_mode_failures(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    staging = _synthetic_staging(tmp_path, monkeypatch)
    target = staging / intake.PDF_FILENAME
    link = staging / "source" / "linked.pdf"
    link.symlink_to(target.name)
    monkeypatch.setattr(intake, "PDF_FILENAME", "source/linked.pdf")
    with pytest.raises(intake.Pliush2005CanonicalGrammarIntakeError, match=r"symbolic-link|regular file"):
        intake.private_audit(staging)

    staging = _synthetic_staging(tmp_path / "mode", monkeypatch)
    bad = staging / intake.PDF_FILENAME
    os.chmod(bad, 0o400)
    with pytest.raises(intake.Pliush2005CanonicalGrammarIntakeError, match="mode 0600"):
        intake.private_audit(staging)


def test_private_audit_rejects_hash_drift(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    staging = _synthetic_staging(tmp_path, monkeypatch)
    path = staging / intake.PDF_FILENAME
    path.write_bytes(b"drifted-bytes")
    os.chmod(path, 0o600)
    with pytest.raises(intake.Pliush2005CanonicalGrammarIntakeError, match="hash drift"):
        intake.private_audit(staging)


def test_private_audit_succeeds_with_synthetic_inputs(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    staging = _synthetic_staging(tmp_path, monkeypatch)
    result = intake.private_audit(staging)
    assert result["ok"] is True
    assert result["staging_root"] == intake.PRIVATE_INPUT_LOCATOR
    assert result["artifact_count"] == 6
    assert "GoogleDrive-" not in intake.canonical_json(result)
    assert "/Users/" not in intake.canonical_json(result)


def test_deterministic_cli_mint_and_check(tmp_path: Path) -> None:
    out = tmp_path / "git" / "receipt.json"
    out.parent.mkdir(parents=True)
    (out.parent / ".git").mkdir()
    mint = subprocess.run(
        [sys.executable, str(intake.SCRIPT_PATH), "--mint", "--write", str(out)],
        check=False,
        capture_output=True,
        text=True,
    )
    assert mint.returncode == 0, mint.stdout + mint.stderr
    mint_payload = json.loads(mint.stdout)
    assert mint_payload["ok"] is True
    assert mint_payload["status"] == intake.STATUS
    assert out.is_file()
    check = subprocess.run(
        [sys.executable, str(intake.SCRIPT_PATH), "--check", str(out)],
        check=False,
        capture_output=True,
        text=True,
    )
    assert check.returncode == 0, check.stdout + check.stderr
    check_payload = json.loads(check.stdout)
    assert check_payload["receipt_sha256"] == mint_payload["receipt_sha256"]


def test_check_cli_is_hermetic_without_drive(monkeypatch: pytest.MonkeyPatch) -> None:
    if not PUBLIC_RECEIPT.is_file():
        pytest.skip("public receipt not materialized yet")

    def boom() -> Path:
        raise intake.Pliush2005CanonicalGrammarIntakeError("drive must not be touched")

    monkeypatch.setattr(intake, "default_staging_root", boom)
    assert intake.main(["--check", str(PUBLIC_RECEIPT)]) == 0


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
    assert validated["page_map"]["morphemics"]["pdf_end"] == 20
    assert validated["rights"]["public_full_text_export"] is False
    dumped = json.dumps(validated, ensure_ascii=False)
    assert "GoogleDrive-" not in dumped
    assert "@gmail.com" not in dumped
    assert "/Users/" not in dumped
    assert "page_texts" not in validated


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
        drive_staging / intake.ITEM_HTML_FILENAME,
        drive_staging / intake.ONLINE_BOOK_HTML_FILENAME,
        drive_staging / intake.PDF_HEADERS_FILENAME,
        drive_staging / intake.ITEM_HEADERS_FILENAME,
        drive_staging / intake.ONLINE_BOOK_HEADERS_FILENAME,
    ]
    if not all(path.exists() for path in required):
        pytest.skip("Drive custody artifacts unavailable")
    result = intake.private_audit(drive_staging)
    assert result["ok"] is True
    assert result["artifact_count"] == 6
    assert result["provider_identity_sha256"] == intake.AUTHORITATIVE_GOOGLE_DRIVE_PROVIDER_IDENTITY_SHA256
