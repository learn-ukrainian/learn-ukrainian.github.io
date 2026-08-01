"""Tests for the complete, fail-closed existing-corpus admission pass."""

from __future__ import annotations

import copy
import hashlib
import json
import sqlite3
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator, FormatChecker

from scripts.projects.open_model_data import admit_existing_corpus as admission
from scripts.projects.open_model_data.model_view_exporter import (
    DEFAULT_V011_MANIFEST,
    v011_items,
)
from scripts.projects.open_model_data.validate_source_records import validate_path

ROOT = Path(__file__).resolve().parents[1]


def _json(path: Path, value: object) -> None:
    path.write_text(admission.canonical_json(value) + "\n", encoding="utf-8")


def _database(path: Path, rows: list[tuple[str, str, str]]) -> None:
    with sqlite3.connect(path) as connection:
        connection.execute(
            "CREATE TABLE documents (id INTEGER PRIMARY KEY, source TEXT NOT NULL, work TEXT NOT NULL, text TEXT NOT NULL, author TEXT NOT NULL)"
        )
        connection.executemany("INSERT INTO documents(source, work, text, author) VALUES (?, ?, ?, ?)", rows)


def _profile(*, expected_rows: int, expected_words: int) -> dict[str, object]:
    return {"schema_version": "corpus_profile_config_v1", "profile_id": "fixture-profile-v1", "source_snapshot_id": "fixture-snapshot-v1", "record_batch_size": 16, "top_unknown_limit": 0,
            "vesum": {"database": "unused.db", "snapshot_id": "fixture-vesum-v1", "interface": "scripts.verification.vesum.verify_words", "batch_size": 1},
            "sources": [{"source_family": "fixture_documents", "inventory_asset_id": "db.fixture", "adapter": {"kind": "sqlite_query_v1", "database": "sources.db", "table": "documents", "id_column": "id", "text_column": "text", "locator_column": "id", "dimensions": {"period": {"constant": "modern"}, "genre": {"constant": "fixture"}, "register": {"constant": "neutral"}, "origin": {"constant": "human_authored_source"}}}, "evidence": {"provenance_status": "partial", "rights_status": "not_reconstructed", "origin_status": "inventory_classified", "contamination_status": "not_checked", "permitted_use": "provenance_investigation"}, "expected": {"rows": expected_rows, "lexical_words": expected_words}}]}


def _config(*, complete_evidence: bool = False, destination: str | None = None) -> dict[str, object]:
    evidence = {key: "complete" for key in ("provenance", "acquisition", "snapshot", "rights", "origin", "contamination")}
    if not complete_evidence:
        evidence["rights"] = "not_reconstructed"
    return {"schema_version": "corpus_admission_config_v1", "admission_id": "fixture-admission-v1", "profile_config": "profile.json", "evidence_packet": None, "families": [{"source_family": "fixture_documents", "source_group_column": "source", "work_group_column": "work", "attributes": {"author": {"column": "author"}, "genre": {"constant": "fixture"}, "origin": {"constant": "human_authored_source"}, "period": {"constant": "modern"}, "region": {"constant": "unknown"}, "register": {"constant": "neutral"}, "translation_origin": {"constant": "unknown"}}, "evidence": evidence, "proposed_destination": destination, "source_record": None}]}


def _run(tmp_path: Path, suffix: str, **kwargs: object) -> admission.AdmissionRun:
    _json(tmp_path / "profile.json", _profile(expected_rows=int(kwargs.pop("expected_rows", 2)), expected_words=int(kwargs.pop("expected_words", 4))))
    _json(tmp_path / "config.json", _config(**kwargs))
    return admission.admit_corpus(config_path=tmp_path / "config.json", input_root=tmp_path, manifest_output=tmp_path / f"manifest-{suffix}.jsonl", receipt_output=tmp_path / f"receipt-{suffix}.json")


def test_unknown_evidence_fails_closed_and_is_byte_stable(tmp_path: Path) -> None:
    _database(tmp_path / "sources.db", [("s1", "w1", "два слова", "Автор"), ("s2", "w2", "ще два", "Автор")])
    first = _run(tmp_path, "first")
    second = _run(tmp_path, "second")

    assert first.complete is True
    assert first.receipt["dispositions"]["unresolved"] == {"rows": 2, "lexical_words": 4}
    assert first.receipt["training_eligible_emitted"] is False
    assert (tmp_path / "receipt-first.json").read_bytes() == (tmp_path / "receipt-second.json").read_bytes()
    assert (tmp_path / "manifest-first.jsonl").read_bytes() == (tmp_path / "manifest-second.jsonl").read_bytes()
    manifest = (tmp_path / "manifest-first.jsonl").read_text(encoding="utf-8")
    assert "/" not in manifest
    first_row = json.loads(manifest.splitlines()[0])
    assert first_row["attributes"]["origin"] == "human_authored_source"
    assert first_row["evidence_state"]["contamination"] == "complete"


def test_complete_evidence_is_only_proposed_until_operator_acceptance(tmp_path: Path) -> None:
    _database(tmp_path / "sources.db", [("s1", "w1", "два слова", "Автор"), ("s2", "w2", "ще два", "Автор")])
    result = _run(tmp_path, "proposed", complete_evidence=True, destination="continued_pretraining")

    assert result.receipt["dispositions"]["proposed_admission"] == {"rows": 2, "lexical_words": 4}
    rows = [json.loads(line) for line in (tmp_path / "manifest-proposed.jsonl").read_text(encoding="utf-8").splitlines()]
    assert {row["disposition"] for row in rows} == {"proposed_admission"}
    assert all(row["reasons"] == ["operator_acceptance_required"] for row in rows)
    assert result.receipt["training_eligible_emitted"] is False


def test_evaluation_isolation_and_denominator_mismatch_are_explicit(tmp_path: Path) -> None:
    evaluation_text = v011_items(DEFAULT_V011_MANIFEST)[0]["source"]
    _database(tmp_path / "sources.db", [("s1", "w1", evaluation_text, "Автор"), ("s2", "w2", "ще два", "Автор")])
    expected_words = len(admission.WORD_RE.findall(evaluation_text)) + 2
    result = _run(tmp_path, "isolated", complete_evidence=True, destination="continued_pretraining", expected_rows=3, expected_words=expected_words)

    assert result.complete is False
    assert result.receipt["coverage"]["processed_rows"] == 2
    assert result.receipt["coverage"]["expected_rows"] == 3
    assert result.receipt["dispositions"]["excluded"]["rows"] == 1
    assert result.receipt["dispositions"]["proposed_admission"]["rows"] == 1


def test_missing_database_emits_empty_fail_closed_receipt(tmp_path: Path) -> None:
    _json(tmp_path / "profile.json", _profile(expected_rows=2, expected_words=4))
    _json(tmp_path / "config.json", _config())
    manifest = tmp_path / "manifest.jsonl"
    source_records = tmp_path / "source-records.jsonl"
    receipt = tmp_path / "receipt.json"
    manifest.write_bytes(b"stale manifest\n")
    source_records.write_bytes(b"stale source records\n")
    receipt.write_bytes(b"stale receipt\n")

    result = admission.admit_corpus(
        config_path=tmp_path / "config.json",
        input_root=tmp_path,
        manifest_output=manifest,
        source_record_output=source_records,
        receipt_output=receipt,
    )

    assert result.complete is False
    assert result.receipt["coverage"]["inaccessible_families"] == [{"reason": "FileNotFoundError", "source_family": "fixture_documents"}]
    assert result.receipt["outputs"]["manifest"]["records"] == 0
    assert manifest.read_bytes() == b""
    assert source_records.read_bytes() == b""
    assert json.loads(receipt.read_text(encoding="utf-8"))["coverage"]["complete"] is False


def test_coverage_denominator_uses_only_configured_profile_families(tmp_path: Path) -> None:
    _database(tmp_path / "sources.db", [("s1", "w1", "два слова", "Автор"), ("s2", "w2", "ще два", "Автор")])
    profile = _profile(expected_rows=2, expected_words=4)
    extra = copy.deepcopy(profile["sources"][0])  # type: ignore[index]
    extra["source_family"] = "unconfigured_extra"
    extra["expected"] = {"rows": 99, "lexical_words": 999}
    profile["sources"].append(extra)  # type: ignore[union-attr]
    _json(tmp_path / "profile.json", profile)
    _json(tmp_path / "config.json", _config())

    result = admission.admit_corpus(
        config_path=tmp_path / "config.json",
        input_root=tmp_path,
        manifest_output=tmp_path / "manifest.jsonl",
        receipt_output=tmp_path / "receipt.json",
    )

    assert result.complete is True
    assert result.receipt["coverage"]["expected_rows"] == 2
    assert result.receipt["coverage"]["expected_lexical_words"] == 4


def test_duplicate_source_family_config_is_rejected(tmp_path: Path) -> None:
    _database(tmp_path / "sources.db", [("s1", "w1", "два слова", "Автор")])
    config = _config()
    config["families"].append(dict(config["families"][0]))  # type: ignore[index]
    _json(tmp_path / "profile.json", _profile(expected_rows=1, expected_words=2))
    _json(tmp_path / "config.json", config)

    with pytest.raises(admission.AdmissionError, match="duplicate"):
        admission.admit_corpus(config_path=tmp_path / "config.json", input_root=tmp_path, manifest_output=tmp_path / "manifest.jsonl", receipt_output=tmp_path / "receipt.json")


def _wikipedia_fixture(tmp_path: Path) -> tuple[Path, Path]:
    timestamps = ("2026-04-11T00:59:17+00:00", "2026-04-11T01:00:17+00:00")
    with sqlite3.connect(tmp_path / "sources.db") as connection:
        connection.execute(
            "CREATE TABLE wikipedia (id INTEGER PRIMARY KEY, title TEXT, url TEXT, text TEXT, char_count INTEGER, fetched_at TEXT)"
        )
        connection.executemany(
            "INSERT INTO wikipedia(title, url, text, char_count, fetched_at) VALUES (?, ?, ?, ?, ?)",
            [
                ("Стаття один", "https://uk.wikipedia.org/wiki/Стаття_один", "два слова", 10, timestamps[0]),
                ("Стаття два", "https://uk.wikipedia.org/wiki/Стаття_два", "ще два", 7, timestamps[1]),
            ],
        )
    profile = _profile(expected_rows=2, expected_words=4)
    source = profile["sources"][0]  # type: ignore[index]
    source["source_family"] = "wikipedia"
    source["adapter"].update({"table": "wikipedia", "id_column": "id", "text_column": "text"})  # type: ignore[union-attr]
    _json(tmp_path / "profile.json", profile)

    evidence = {
        "schema_version": "corpus_admission_evidence_v1",
        "evidence_packet_id": "evidence.wikipedia_fixture_v1",
        "retrieved_on": "2026-08-01",
        "sources": [{
            "source_record_evidence_id": "source.wikipedia_fixture_v1", "source_family": "wikipedia",
            "snapshot": {"kind": "article_level_captured_snapshot", "rows": 2, "lexical_words": 4, "capture_timestamps": 2, "first_retrieved_at": timestamps[0], "last_retrieved_at": timestamps[1], "content_hash_scope": "exact UTF-8 bytes", "revision_id_required_by_contract": False},
            "acquisition": {"method": "fixture MediaWiki capture", "api_endpoint": "https://uk.wikipedia.org/w/api.php", "api_parameters": {"action": "query", "prop": "extracts", "explaintext": "1"}, "code_cohorts": [{"evidence_id": "code.wikipedia_fixture", "rows": 2, "first_retrieved_at": timestamps[0], "last_retrieved_at": timestamps[1], "commit": "a" * 40, "git_blob_oid": "b" * 40, "sha256": "c" * 64, "url": "https://example.invalid/fetch.py"}]},
            "bibliographic": {"editor": "Wikipedia contributors", "publisher": "Ukrainian Wikipedia community, hosted by the Wikimedia Foundation", "translation_origin": "unknown"},
            "description": {"author": "Wikipedia contributors", "period": "modern", "genre": "encyclopedia", "register": "reference", "region": "unknown"},
            "rights": {"status": "granted", "jurisdiction": "international", "license_expression": "CC-BY-SA-4.0", "license_terms_evidence_id": "rights.cc_by_sa_4.0_legalcode", "evidence_ids": ["rights.cc_by_sa_4.0_legalcode"], "legal_conclusion": "not_asserted", "operational_permission": "share and adapt for any purpose subject to license conditions", "obligations": ["attribute and share alike"], "material_ambiguities": ["other rights are not certified"]},
            "evidence": [
                {"evidence_id": "rights.cc_by_sa_4.0_legalcode", "citation": "CC BY-SA 4.0 legal code", "canonical_url": "https://creativecommons.org/licenses/by-sa/4.0/legalcode", "receipt_url": "https://creativecommons.org/licenses/by-sa/4.0/legalcode.txt", "retrieved_on": "2026-08-01", "sha256": "d" * 64},
                {"evidence_id": "code.wikipedia_fixture", "citation": "fixture acquisition code", "canonical_url": "https://example.invalid/fetch.py", "receipt_url": "https://example.invalid/fetch.py", "retrieved_on": "2026-08-01", "sha256": "c" * 64},
            ],
            "review": {"reviewer_id": "advisor.sol_fixture", "qualification": "operational provenance and license review, not legal advice", "confidence": "medium", "unresolved": False},
        }],
    }
    _json(tmp_path / "evidence.json", evidence)
    config = {
        "schema_version": "corpus_admission_config_v1", "admission_id": "fixture-wikipedia-v1", "profile_config": "profile.json", "evidence_packet": "evidence.json",
        "families": [{"source_family": "wikipedia", "source_group_column": "fetched_at", "work_group_column": "title", "attributes": {"author": {"constant": "Wikipedia contributors"}, "genre": {"constant": "encyclopedia"}, "origin": {"constant": "human_authored_source"}, "period": {"constant": "modern"}, "region": {"constant": "unknown"}, "register": {"constant": "reference"}, "translation_origin": {"constant": "unknown"}}, "evidence": {key: "complete" for key in ("provenance", "acquisition", "snapshot", "rights", "origin", "contamination")}, "proposed_destination": "open_weight_ukrainian_continued_pretraining_text_v1", "source_record": {"evidence_source_id": "source.wikipedia_fixture_v1", "title_column": "title", "url_column": "url", "retrieved_at_column": "fetched_at"}}],
    }
    _json(tmp_path / "config.json", config)
    return tmp_path / "config.json", tmp_path / "source-records.jsonl"


def test_wikipedia_source_records_are_contract_valid_pending_and_deterministic(tmp_path: Path) -> None:
    config, source_records = _wikipedia_fixture(tmp_path)
    first = admission.admit_corpus(config_path=config, input_root=tmp_path, manifest_output=tmp_path / "manifest-1.jsonl", receipt_output=tmp_path / "receipt-1.json", source_record_output=source_records)
    second = admission.admit_corpus(config_path=config, input_root=tmp_path, manifest_output=tmp_path / "manifest-2.jsonl", receipt_output=tmp_path / "receipt-2.json", source_record_output=tmp_path / "source-records-2.jsonl")

    assert first.receipt["dispositions"]["proposed_admission"] == {"rows": 2, "lexical_words": 4}
    assert first.receipt["outputs"]["source_records"]["records"] == 2
    assert first.receipt["families"][0]["source_record_evidence"] == {"capture_timestamps": 2, "code_cohorts": {"code.wikipedia_fixture": 2}, "first_retrieved_at": "2026-04-11T00:59:17+00:00", "last_retrieved_at": "2026-04-11T01:00:17+00:00", "matches_snapshot": True, "records": 2}
    validation = validate_path(source_records)
    assert validation["admitted_records"] == 0
    assert validation["rejected_records"] == 2
    assert validation["rejection_reason_counts"] == {"record_marked_excluded": 2}
    records = [json.loads(line) for line in source_records.read_text(encoding="utf-8").splitlines()]
    assert records[0]["content"]["sha256"] == hashlib.sha256("два слова".encode()).hexdigest()
    assert records[0]["acquisition"]["source_or_catalog_url"].startswith("https://uk.wikipedia.org/wiki/")
    assert records[0]["bibliographic"]["translation_origin"] == "unknown"
    assert records[0]["description"]["register"] == "reference"
    assert records[0]["rights"]["model_training"]["legal_conclusion"] == "not_asserted"
    assert {record["usage"]["role"] for record in records} == {"excluded"}
    assert first.receipt["training_eligible_emitted"] is False
    assert (tmp_path / "manifest-1.jsonl").read_bytes() == (tmp_path / "manifest-2.jsonl").read_bytes()
    assert source_records.read_bytes() == (tmp_path / "source-records-2.jsonl").read_bytes()
    assert (tmp_path / "receipt-1.json").read_bytes() == (tmp_path / "receipt-2.json").read_bytes()
    assert first.receipt == second.receipt


def test_source_record_validation_failure_leaves_no_final_artifacts(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config, source_records = _wikipedia_fixture(tmp_path)
    manifest = tmp_path / "manifest.jsonl"
    receipt = tmp_path / "receipt.json"
    monkeypatch.setattr(
        admission,
        "validate_source_record_path",
        lambda _path: {
            "admitted_records": 0,
            "rejected_records": 2,
            "input_sha256": "0" * 64,
            "rejection_reason_counts": {"record_marked_excluded": 2},
        },
    )

    with pytest.raises(admission.AdmissionError, match="pending source-record manifest"):
        admission.admit_corpus(
            config_path=config,
            input_root=tmp_path,
            manifest_output=manifest,
            receipt_output=receipt,
            source_record_output=source_records,
        )

    assert not manifest.exists()
    assert not source_records.exists()
    assert not receipt.exists()


def test_receipt_validation_failure_leaves_no_final_artifacts(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _database(tmp_path / "sources.db", [("s1", "w1", "два слова", "Автор")])
    _json(tmp_path / "profile.json", _profile(expected_rows=1, expected_words=2))
    _json(tmp_path / "config.json", _config())
    manifest = tmp_path / "manifest.jsonl"
    receipt = tmp_path / "receipt.json"
    original_validate = admission._validate

    def fail_receipt(value: object, validator: object, label: str) -> None:
        if label == "admission receipt":
            raise admission.AdmissionError("forced receipt validation failure")
        original_validate(value, validator, label)  # type: ignore[arg-type]

    monkeypatch.setattr(admission, "_validate", fail_receipt)
    with pytest.raises(admission.AdmissionError, match="forced receipt validation failure"):
        admission.admit_corpus(
            config_path=tmp_path / "config.json",
            input_root=tmp_path,
            manifest_output=manifest,
            receipt_output=receipt,
        )

    assert not manifest.exists()
    assert not receipt.exists()


def test_receipt_promotion_failure_restores_prior_artifacts(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _database(tmp_path / "sources.db", [("s1", "w1", "два слова", "Автор")])
    _json(tmp_path / "profile.json", _profile(expected_rows=1, expected_words=2))
    _json(tmp_path / "config.json", _config())
    manifest = tmp_path / "manifest.jsonl"
    receipt = tmp_path / "receipt.json"
    manifest.write_bytes(b"prior manifest\n")
    receipt.write_bytes(b"prior receipt\n")
    original_replace = admission.os.replace
    failed = False

    def fail_receipt_promotion(source: Path, destination: Path) -> None:
        nonlocal failed
        if Path(destination) == receipt and not failed:
            failed = True
            raise OSError("forced receipt promotion failure")
        original_replace(source, destination)

    monkeypatch.setattr(admission.os, "replace", fail_receipt_promotion)
    with pytest.raises(OSError, match="forced receipt promotion failure"):
        admission.admit_corpus(
            config_path=tmp_path / "config.json",
            input_root=tmp_path,
            manifest_output=manifest,
            receipt_output=receipt,
        )

    assert manifest.read_bytes() == b"prior manifest\n"
    assert receipt.read_bytes() == b"prior receipt\n"
    assert not list(tmp_path.glob("*.rollback"))


def test_real_wikipedia_terms_receipts_and_operator_gate_are_frozen() -> None:
    contracts = ROOT / "data/projects/open_model_data/contracts"
    evidence = json.loads((ROOT / "data/projects/open_model_data/admission/wikipedia_primary_rights_evidence_v1.json").read_text())
    packet = json.loads((ROOT / "data/projects/open_model_data/admission/public_external_operator_decision_packet_v1.json").read_text())
    evidence_schema = json.loads((contracts / "corpus_admission_evidence_v1.schema.json").read_text())
    packet_schema = json.loads((contracts / "corpus_admission_operator_packet_v1.schema.json").read_text())
    assert not list(Draft202012Validator(evidence_schema, format_checker=FormatChecker()).iter_errors(evidence))
    assert not list(Draft202012Validator(packet_schema, format_checker=FormatChecker()).iter_errors(packet))
    items = {item["evidence_id"]: item for item in evidence["sources"][0]["evidence"]}
    assert items["rights.wikimedia_terms_554852"]["sha256"] == "bbb5ebfb89700c0e4732109cddbd45e6d8d2ba5dc339b206c7c5089ec4a4812b"
    assert items["rights.cc_by_sa_4.0_legalcode"]["sha256"] == "28a9529c7d0bb4dc51f4bf5c116a3d16ef247a052f7591466768ddf563fd1cf5"
    assert evidence["sources"][0]["snapshot"] == {"capture_timestamps": 183, "content_hash_scope": "SHA-256 of the exact UTF-8 bytes of wikipedia.text as stored in data/sources.db", "first_retrieved_at": "2026-04-11T00:59:17.337039+00:00", "kind": "article_level_captured_snapshot", "last_retrieved_at": "2026-07-07T13:47:23.791310+00:00", "lexical_words": 2865506, "revision_id_required_by_contract": False, "rows": 1029}
    assert packet["operator_decision_status"] == "pending"
    assert packet["families"][-1]["current_disposition"] == "proposed_admission"
    assert packet["families"][-1]["proposed_destination"] == "open_weight_ukrainian_continued_pretraining_text_v1"
    assert packet["decision_required"] is True
