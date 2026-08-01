"""Tests for the complete, fail-closed existing-corpus admission pass."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pytest

from scripts.projects.open_model_data import admit_existing_corpus as admission
from scripts.projects.open_model_data.model_view_exporter import (
    DEFAULT_V011_MANIFEST,
    v011_items,
)


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
    return {"schema_version": "corpus_admission_config_v1", "admission_id": "fixture-admission-v1", "profile_config": "profile.json", "families": [{"source_family": "fixture_documents", "source_group_column": "source", "work_group_column": "work", "attributes": {"author": {"column": "author"}, "genre": {"constant": "fixture"}, "origin": {"constant": "human_authored_source"}, "period": {"constant": "modern"}, "region": {"constant": "unknown"}, "register": {"constant": "neutral"}, "translation_origin": {"constant": "unknown"}}, "evidence": evidence, "proposed_destination": destination}]}


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
    result = _run(tmp_path, "missing")

    assert result.complete is False
    assert result.receipt["coverage"]["inaccessible_families"] == [{"reason": "FileNotFoundError", "source_family": "fixture_documents"}]
    assert result.receipt["outputs"]["manifest"]["records"] == 0


def test_duplicate_source_family_config_is_rejected(tmp_path: Path) -> None:
    _database(tmp_path / "sources.db", [("s1", "w1", "два слова", "Автор")])
    config = _config()
    config["families"].append(dict(config["families"][0]))  # type: ignore[index]
    _json(tmp_path / "profile.json", _profile(expected_rows=1, expected_words=2))
    _json(tmp_path / "config.json", config)

    with pytest.raises(admission.AdmissionError, match="duplicate"):
        admission.admit_corpus(config_path=tmp_path / "config.json", input_root=tmp_path, manifest_output=tmp_path / "manifest.jsonl", receipt_output=tmp_path / "receipt.json")
