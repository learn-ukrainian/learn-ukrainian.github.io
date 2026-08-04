"""Focused contract tests for the text-free VESUM-unattested sampler."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from scripts.projects.open_model_data import document_signal_manifest as phase1
from scripts.projects.open_model_data import vesum_unattested_sample as samples

ROOT = Path(__file__).resolve().parents[1]
FAMILIES = ("literary", "public_textbooks", "external_articles", "wikipedia")


def _write(path: Path, value: object) -> None:
    path.write_text(samples.canonical_json(value) + "\n", encoding="utf-8")


def _source_spec(family: str) -> dict:
    return {
        "source_family": family,
        "inventory_asset_id": f"db.{family}",
        "adapter": {
            "kind": "sqlite_query_v1",
            "database": "sources.db",
            "table": "documents",
            "id_column": "id",
            "text_column": "text",
            "locator_column": "locator",
            "dimensions": {
                "period": {"column": "period"},
                "genre": {"column": "genre"},
                "register": {"column": "register"},
                "origin": {"constant": "human_authored_source"},
            },
        },
        "evidence": {
            "provenance_status": "partial",
            "rights_status": "not_reconstructed",
            "origin_status": "inventory_classified",
            "contamination_status": "not_checked",
            "permitted_use": "provenance_investigation",
        },
        "expected": {"rows": 2, "lexical_words": 4},
    }


def _fixture(tmp_path: Path) -> dict[str, Path]:
    source_db, vesum_db = tmp_path / "sources.db", tmp_path / "vesum.db"
    with sqlite3.connect(source_db) as connection:
        connection.execute(
            "CREATE TABLE documents (id INTEGER, locator TEXT, text TEXT, period TEXT, genre TEXT, register TEXT, source TEXT, work TEXT)"
        )
        connection.executemany(
            "INSERT INTO documents VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            [
                (1, "one", "відомий невідомий", "modern", "prose", "neutral", "source-a", "work-a"),
                (2, "two", "відомий неатестований", "historical", "poetry", "literary", "source-b", "work-b"),
            ],
        )
    with sqlite3.connect(vesum_db) as connection:
        connection.execute("CREATE TABLE forms (word_form TEXT, lemma TEXT, tags TEXT, pos TEXT)")
        connection.execute("INSERT INTO forms VALUES ('відомий', 'відомий', '', 'adj')")

    sources = [_source_spec(family) for family in FAMILIES]
    phase1_sources = []
    for source in sources:
        copied = json.loads(json.dumps(source))
        copied["adapter"]["dimensions"]["origin"] = {"constant": "human_authored_source"}
        phase1_sources.append(copied)
    _write(tmp_path / "phase1-profile.json", {"sources": phase1_sources})
    _write(
        tmp_path / "admission.json",
        {
            "families": [
                {
                    "source_family": family,
                    "source_group_column": "source",
                    "work_group_column": "work",
                    "evidence": {
                        "provenance": "accepted",
                        "rights": "accepted",
                        "origin": "known",
                        "contamination": "not_checked",
                        "acquisition": "accepted",
                        "snapshot": "accepted",
                    },
                }
                for family in FAMILIES
            ]
        },
    )
    _write(
        tmp_path / "admission-receipt.json",
        {
            "coverage": {"complete": True},
            "training_eligible_emitted": False,
            "families": [
                {"source_family": family, "actual": {"rows": 2}, "dispositions": {"unresolved": {"rows": 2}}}
                for family in FAMILIES
            ],
        },
    )
    _write(
        tmp_path / "phase1-config.json",
        {
            "schema_version": "document_signal_config_v1",
            "manifest_id": "phase1-fixture",
            "profile_config": "phase1-profile.json",
            "admission_config": "admission.json",
            "admission_receipt": "admission-receipt.json",
        },
    )
    phase1_manifest, phase1_receipt = tmp_path / "phase1.jsonl", tmp_path / "phase1-receipt.json"
    phase1.build_manifest(
        config_path=tmp_path / "phase1-config.json",
        input_root=tmp_path,
        manifest_output=phase1_manifest,
        receipt_output=phase1_receipt,
    )
    _write(
        tmp_path / "profile.json",
        {
            "schema_version": "corpus_profile_config_v1",
            "profile_id": "fixture-profile",
            "source_snapshot_id": "fixture-snapshot",
            "record_batch_size": 2,
            "top_unknown_limit": 1,
            "vesum": {
                "database": "vesum.db",
                "snapshot_id": "fixture-vesum",
                "interface": "scripts.verification.vesum.verify_words",
                "batch_size": 10,
            },
            "sources": sources,
        },
    )
    _write(
        tmp_path / "profile-receipt.json",
        {"coverage": {"complete": True, "processed_rows": 8}, "vesum": {"tokens_unknown": 8}, "schema_version": "fixture-profile-receipt"},
    )
    _write(
        tmp_path / "config.json",
        {
            "schema_version": "vesum_unattested_sample_config_v1",
            "expected_denominator": 8,
            "production_expected_denominator": 9292022,
            "family_quotas": {family: 1 for family in FAMILIES},
        },
    )
    return {
        "config_path": tmp_path / "config.json",
        "profile_path": tmp_path / "profile.json",
        "profile_receipt_path": tmp_path / "profile-receipt.json",
        "phase1_manifest_path": phase1_manifest,
        "phase1_receipt_path": phase1_receipt,
        "source_database": source_db,
        "vesum_database": vesum_db,
        "detector_config_path": ROOT / "data/projects/open_model_data/detector/language_contact_config_v1.json",
    }


def _build(paths: dict[str, Path], output: Path, receipt: Path) -> dict:
    return samples.build_sample(
        **paths,
        output_path=output,
        receipt_path=receipt,
        detector_input_root=ROOT,
    )


def test_build_is_text_free_schema_valid_and_byte_identical(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    paths = _fixture(tmp_path)
    monkeypatch.setattr(samples.detector, "run_detector_on_text", lambda **_kwargs: [])
    first = _build(paths, tmp_path / "first.jsonl", tmp_path / "first-receipt.json")
    second = _build(paths, tmp_path / "second.jsonl", tmp_path / "second-receipt.json")
    assert (tmp_path / "first.jsonl").read_bytes() == (tmp_path / "second.jsonl").read_bytes()
    assert first["denominator"] == 8
    assert first["sample_counts"]["total"] == 4
    records = [json.loads(line) for line in (tmp_path / "first.jsonl").read_text(encoding="utf-8").splitlines()]
    validator = Draft202012Validator(json.loads(samples.RECORD_SCHEMA.read_text(encoding="utf-8")))
    assert all(not list(validator.iter_errors(record)) for record in records)
    assert {record["source"]["source_axes"]["source_family"] for record in records} == set(FAMILIES)
    assert all(record["classification"] == "unresolved" for record in records)
    text_bearing = {"text", "original_text", "surface_form", "raw_payload", "raw_evidence"}
    assert all(not text_bearing.intersection(record) for record in records)
    receipt_validator = Draft202012Validator(json.loads(samples.RECEIPT_SCHEMA.read_text(encoding="utf-8")))
    assert not list(receipt_validator.iter_errors(first))
    assert samples.verify_sample(**paths, output_path=tmp_path / "first.jsonl", receipt_path=tmp_path / "first-receipt.json") == first


@pytest.mark.parametrize("mutation", ("denominator", "pin", "counts"))
def test_verify_fails_closed_on_receipt_tampering(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, mutation: str
) -> None:
    paths = _fixture(tmp_path)
    monkeypatch.setattr(samples.detector, "run_detector_on_text", lambda **_kwargs: [])
    output, receipt_path = tmp_path / "sample.jsonl", tmp_path / "receipt.json"
    _build(paths, output, receipt_path)
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    if mutation == "denominator":
        receipt["denominator"] += 1
    elif mutation == "counts":
        receipt["sample_counts"]["total"] += 1
    else:
        receipt["pins"]["vesum_sha256"] = "0" * 64
    _write(receipt_path, receipt)
    with pytest.raises(samples.SampleError):
        samples.verify_sample(**paths, output_path=output, receipt_path=receipt_path)


def test_vesum_non_hit_never_becomes_an_automatic_error() -> None:
    assert samples._detector_bucket("") == "unresolved"
    assert samples._detector_bucket("unknown_future_detector_category") == "unresolved"
    assert samples._detector_bucket("valid_word_contact_candidate") == "unresolved"


def test_verify_rejects_nested_text_field(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    paths = _fixture(tmp_path)
    monkeypatch.setattr(samples.detector, "run_detector_on_text", lambda **_kwargs: [])
    output, receipt_path = tmp_path / "sample.jsonl", tmp_path / "receipt.json"
    _build(paths, output, receipt_path)
    record = json.loads(output.read_text(encoding="utf-8").splitlines()[0])
    record["source"]["source_axes"]["text"] = "forbidden"
    output.write_text(samples.canonical_json(record) + "\n", encoding="utf-8")
    with pytest.raises(samples.SampleError):
        samples.verify_sample(**paths, output_path=output, receipt_path=receipt_path)


def test_build_rejects_profile_receipt_denominator_drift(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    paths = _fixture(tmp_path)
    monkeypatch.setattr(samples.detector, "run_detector_on_text", lambda **_kwargs: [])
    profile_receipt = json.loads(paths["profile_receipt_path"].read_text(encoding="utf-8"))
    profile_receipt["vesum"]["tokens_unknown"] = 7
    _write(paths["profile_receipt_path"], profile_receipt)
    with pytest.raises(samples.SampleError, match="profile receipt unattested denominator"):
        _build(paths, tmp_path / "sample.jsonl", tmp_path / "receipt.json")


def test_build_rejects_incomplete_phase1_row_coverage(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    paths = _fixture(tmp_path)
    monkeypatch.setattr(samples.detector, "run_detector_on_text", lambda **_kwargs: [])
    with sqlite3.connect(paths["source_database"]) as connection:
        connection.execute("DELETE FROM documents WHERE id = 2")
    with pytest.raises(samples.SampleError, match="Phase 1 row coverage mismatch"):
        _build(paths, tmp_path / "sample.jsonl", tmp_path / "receipt.json")
