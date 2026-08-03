"""Behavioral canaries for the text-free document-signal manifest."""

from __future__ import annotations

import hashlib
import json
import sqlite3
from pathlib import Path

import pytest

from scripts.projects.open_model_data import document_signal_manifest as signals
from scripts.projects.open_model_data.model_view_exporter import DEFAULT_V011_MANIFEST, v011_items


def _write(path: Path, value: object) -> None:
    path.write_text(signals.canonical_json(value) + "\n", encoding="utf-8")


def _fixture(tmp_path: Path, rows: list[tuple[str, str, str, str, str, str]] | None = None) -> tuple[Path, Path, Path]:
    rows = rows or [
        (
            "source-a",
            "work-a",
            "розділ\nрозділ\nhttps://example.invalid/x ІЇЄҐ ёыэъ ’\u0301\ufffd",
            "modern",
            "literary",
            "heritage",
        ),
        ("source-a", "work-a", "точний дублікат", "historical", "article", "dialectal"),
        ("source-b", "work-b", "точний дублікат", "modern", "article", "neutral"),
    ]
    with sqlite3.connect(tmp_path / "sources.db") as connection:
        connection.execute(
            "CREATE TABLE documents (id INTEGER PRIMARY KEY, source TEXT, work TEXT, text TEXT, period TEXT, genre TEXT, register TEXT)"
        )
        connection.executemany(
            "INSERT INTO documents(source, work, text, period, genre, register) VALUES (?, ?, ?, ?, ?, ?)", rows
        )
    profile = {
        "sources": [
            {
                "source_family": "fixture",
                "inventory_asset_id": "db.fixture",
                "evidence": {
                    "rights_status": "not_reconstructed",
                    "permitted_use": "provenance_investigation",
                    "origin_status": "inventory_classified",
                    "contamination_status": "not_checked",
                },
                "expected": {"rows": len(rows)},
                "adapter": {
                    "database": "sources.db",
                    "table": "documents",
                    "id_column": "id",
                    "text_column": "text",
                    "locator_column": "id",
                    "dimensions": {
                        "period": {"column": "period"},
                        "genre": {"column": "genre"},
                        "register": {"column": "register"},
                        "origin": {"constant": "human_authored_source"},
                    },
                },
            }
        ]
    }
    admission = {
        "families": [
            {
                "source_family": "fixture",
                "source_group_column": "source",
                "work_group_column": "work",
                "evidence": {
                    "provenance": "partial",
                    "rights": "not_reconstructed",
                    "origin": "partial",
                    "contamination": "not_checked",
                    "acquisition": "partial",
                    "snapshot": "partial",
                },
            }
        ]
    }
    receipt = {
        "coverage": {"complete": True},
        "training_eligible_emitted": False,
        "families": [
            {
                "source_family": "fixture",
                "actual": {"rows": len(rows)},
                "dispositions": {"unresolved": {"rows": len(rows)}},
            }
        ],
    }
    config = {
        "schema_version": "document_signal_config_v1",
        "manifest_id": "fixture-document-signal-v1",
        "profile_config": "profile.json",
        "admission_config": "admission.json",
        "admission_receipt": "admission-receipt.json",
    }
    _write(tmp_path / "profile.json", profile)
    _write(tmp_path / "admission.json", admission)
    _write(tmp_path / "admission-receipt.json", receipt)
    _write(tmp_path / "config.json", config)
    return tmp_path / "config.json", tmp_path / "manifest.jsonl", tmp_path / "receipt.json"


def _run(tmp_path: Path) -> tuple[list[dict], dict, Path, Path]:
    config, manifest, receipt = _fixture(tmp_path)
    result = signals.build_manifest(
        config_path=config, input_root=tmp_path, manifest_output=manifest, receipt_output=receipt
    )
    return [json.loads(line) for line in manifest.read_text(encoding="utf-8").splitlines()], result, manifest, receipt


def test_fixture_canaries_cover_manifest_contract(tmp_path: Path) -> None:
    rows, receipt, manifest, receipt_path = _run(tmp_path)
    first, second, third = rows
    body = manifest.read_text(encoding="utf-8")
    canaries = {
        "completeness": len(rows) == 3,
        "receipt_row_count": receipt["outputs"]["manifest"]["records"] == 3,
        "receipt_hash": receipt["outputs"]["manifest"]["sha256"] == hashlib.sha256(manifest.read_bytes()).hexdigest(),
        "schema_version": all(row["schema_version"] == "document_signal_record_v1" for row in rows),
        "ordinals": [row["ordinal"] for row in rows] == [0, 1, 2],
        "opaque_record_ids": all(
            row["record_id"].startswith("record.fixture.") and len(row["record_id"].rsplit(".", 1)[1]) == 24
            for row in rows
        ),
        "opaque_source_ids": all(row["source_id"].startswith("source.") for row in rows),
        "opaque_work_ids": all(row["work_id"].startswith("work.") for row in rows),
        "no_text": "точний дублікат" not in body,
        "no_source_path": "sources.db" not in body,
        "no_url": "example.invalid" not in body,
        "exact_content_hash": first["content_sha256"]
        == hashlib.sha256("розділ\nрозділ\nhttps://example.invalid/x ІЇЄҐ ёыэъ ’\u0301\ufffd".encode()).hexdigest(),
        "exact_duplicate_count": second["exact_duplicate"]["count"] == third["exact_duplicate"]["count"] == 2,
        "exact_duplicate_group": second["exact_duplicate"]["group_id"] == third["exact_duplicate"]["group_id"],
        "near_fingerprint_stable_shape": len(first["near_duplicate"]["bands"]) == 8,
        "near_unresolved": first["near_duplicate"]["state"] == "unresolved_candidate_only_no_automatic_erasure",
        "rights_evidence_distinct": first["capability_evidence"]["rights_evidence"] == "not_reconstructed",
        "redistribution_not_overclaimed": first["capability_evidence"]["raw_text_redistribution"]
        == "not_decided_by_document_signal_manifest",
        "learning_eligibility_not_overclaimed": first["capability_evidence"]["learning_view_emission"]
        == "not_emitted_by_admission_receipt",
        "admission_disposition_preserved": first["capability_evidence"]["admission_disposition"]
        == "family_all_unresolved",
        "protected_historical_preserved": second["dimensions"]["period"] == "historical",
        "protected_register_preserved": second["dimensions"]["register"] == "dialectal",
        "cyrillic_signal": first["signals"]["counts"]["cyrillic"] > 0,
        "latin_signal": first["signals"]["counts"]["latin"] > 0,
        "ukrainian_signal": first["signals"]["counts"]["ukrainian_specific"] >= 4,
        "russian_signal": first["signals"]["counts"]["russian_specific"] >= 4,
        "normalization_signal": first["signals"]["normalization"]["replacement_characters"] == 1,
        "boilerplate_signal": first["signals"]["boilerplate"]["repeated_nonblank_lines"] == 1,
        "url_signal": first["signals"]["boilerplate"]["url_like_tokens"] == 1,
        "safety_no_model": receipt["safety"]["uses_model"] is False,
        "safety_read_only": receipt["safety"]["source_databases_read_only"] is True,
        "verify_existing": signals.verify_existing(manifest_path=manifest, receipt_path=receipt_path),
    }
    assert len(canaries) >= 24
    assert all(canaries.values()), [name for name, passed in canaries.items() if not passed]


def test_build_is_byte_deterministic_and_near_fingerprint_is_stable(tmp_path: Path) -> None:
    config, manifest, receipt = _fixture(tmp_path)
    signals.build_manifest(config_path=config, input_root=tmp_path, manifest_output=manifest, receipt_output=receipt)
    first_manifest, first_receipt = manifest.read_bytes(), receipt.read_bytes()
    signals.build_manifest(config_path=config, input_root=tmp_path, manifest_output=manifest, receipt_output=receipt)
    assert manifest.read_bytes() == first_manifest
    assert receipt.read_bytes() == first_receipt


def test_incomplete_profile_fails_closed_without_outputs(tmp_path: Path) -> None:
    config, manifest, receipt = _fixture(tmp_path)
    profile = json.loads((tmp_path / "profile.json").read_text(encoding="utf-8"))
    profile["sources"][0]["expected"]["rows"] += 1
    _write(tmp_path / "profile.json", profile)
    with pytest.raises(signals.ManifestError, match="incomplete corpus coverage"):
        signals.build_manifest(
            config_path=config, input_root=tmp_path, manifest_output=manifest, receipt_output=receipt
        )
    assert not manifest.exists()
    assert not receipt.exists()


@pytest.mark.parametrize(
    "tamper", ["hash", "count", "order", "schema", "nested_schema", "receipt_schema", "generator_hash"]
)
def test_verify_existing_rejects_tampered_artifacts(tmp_path: Path, tamper: str) -> None:
    rows, _receipt, manifest, receipt_path = _run(tmp_path)
    if tamper == "hash":
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
        receipt["outputs"]["manifest"]["sha256"] = "0" * 64
        _write(receipt_path, receipt)
    elif tamper == "count":
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
        receipt["outputs"]["manifest"]["records"] = 99
        _write(receipt_path, receipt)
    elif tamper == "order":
        manifest.write_text(
            "\n".join(signals.canonical_json(value) for value in reversed(rows)) + "\n", encoding="utf-8"
        )
    else:
        if tamper == "schema":
            rows[0]["unexpected"] = True
            manifest.write_text("\n".join(signals.canonical_json(value) for value in rows) + "\n", encoding="utf-8")
        elif tamper == "nested_schema":
            rows[0]["signals"]["counts"]["unexpected"] = 1
            manifest.write_text("\n".join(signals.canonical_json(value) for value in rows) + "\n", encoding="utf-8")
        elif tamper == "receipt_schema":
            receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
            receipt["inputs"]["unexpected"] = True
            _write(receipt_path, receipt)
        else:
            receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
            receipt["inputs"]["generator_sha256"] = "0" * 64
            _write(receipt_path, receipt)
    with pytest.raises(signals.ManifestError):
        signals.verify_existing(manifest_path=manifest, receipt_path=receipt_path)


def test_missing_source_column_fails_closed(tmp_path: Path) -> None:
    config, manifest, receipt = _fixture(tmp_path)
    admission = json.loads((tmp_path / "admission.json").read_text(encoding="utf-8"))
    admission["families"][0]["work_group_column"] = "missing"
    _write(tmp_path / "admission.json", admission)
    with pytest.raises(signals.ManifestError, match="missing source columns"):
        signals.build_manifest(
            config_path=config, input_root=tmp_path, manifest_output=manifest, receipt_output=receipt
        )


@pytest.mark.parametrize(
    ("candidate", "method"),
    [("exact", "exact_normalized"), ("near", "character_containment")],
)
def test_heldout_overlap_is_signaled_without_erasure(tmp_path: Path, candidate: str, method: str) -> None:
    heldout = v011_items(DEFAULT_V011_MANIFEST)[0]["source"]
    if candidate == "near":
        heldout = f"prefix {heldout} suffix"
    config, manifest, receipt = _fixture(tmp_path, [("source", "work", heldout, "modern", "fixture", "neutral")])
    signals.build_manifest(config_path=config, input_root=tmp_path, manifest_output=manifest, receipt_output=receipt)
    row = json.loads(manifest.read_text(encoding="utf-8"))
    assert row["heldout_contamination"] == {
        "method": method,
        "semantics": "signal_only_no_automatic_erasure",
        "state": "matched",
    }


def test_similar_texts_share_independent_minhash_candidate_bands() -> None:
    first = " ".join(f"слово{index}" for index in range(30))
    second = first.replace("слово15", "заміна")
    first_bands = set(signals._near_fingerprint(first)["bands"])
    second_bands = set(signals._near_fingerprint(second)["bands"])
    assert first_bands & second_bands
    assert signals._near_fingerprint(first)["fingerprint"] != signals._near_fingerprint(second)["fingerprint"]


def test_staged_manifest_is_removed_when_row_validation_fails(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    config, manifest, receipt = _fixture(tmp_path)
    original_validate = signals._validate

    def fail_rows(value: object, validator: object, label: str) -> None:
        if label == "document signal row":
            raise signals.ManifestError("planted validation failure")
        original_validate(value, validator, label)

    monkeypatch.setattr(signals, "_validate", fail_rows)
    with pytest.raises(signals.ManifestError, match="planted validation failure"):
        signals.build_manifest(
            config_path=config, input_root=tmp_path, manifest_output=manifest, receipt_output=receipt
        )
    assert not list(tmp_path.glob("manifest.jsonl.tmp*"))
    assert not manifest.exists()
    assert not receipt.exists()
